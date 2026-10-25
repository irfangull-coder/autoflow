"""Agents for the AutoFlow starter.

Architecture (kept deliberately simple for Week 1-3):
  Orchestrator -> decides which agent handles a task
  SupportAgent -> RAG answers + order-status lookup
  DataAgent    -> extracts fields from invoice/email text
  ReportingAgent -> daily/weekly summary from the orders table

The draft + approval pattern is the point: agents NEVER send a
message or update a record directly. They return a draft, the
Orchestrator stores it in the approval queue, and only a human
Approve click marks it as sent/approved. That is the safety story
for the FYP demo and thesis.

Later you can replace the template-based draft text in
SupportAgent with a real LLM call. Keep the same return shape
(draft + source + steps) so the API and dashboard do not change.
"""
import re

from .rag import DocumentIndex
from . import store


class SupportAgent:
    def __init__(self, index: DocumentIndex):
        self.index = index

    def answer(self, question: str) -> dict:
        steps = ["SupportAgent: understood the question", "Checked for an order number"]
        # 1) Order-status path: e.g. "mera order 1023 kahan hai?"
        match = re.search(r"\b(\d{3,})\b", question)
        if match and ("order" in question.lower() or "parcel" in question.lower()):
            order = store.get_order(match.group(1))
            steps.append(f"Found order record: {match.group(1)}")
            if order:
                draft = (
                    f"Hello {order['customer']}, your order "
                    f"{order['id']} ({order['product']}) is currently "
                    f"'{order['status']}'. Amount: Rs {order['amount']}."
                )
                return {
                    "agent": "SupportAgent",
                    "draft": draft,
                    "source": f"Orders table, order {order['id']}",
                    "steps": steps,
                }
            return {
                "agent": "SupportAgent",
                "draft": "Sorry, no record was found for this order number. "
                "Please check the order number and try again.",
                "source": "Orders table (no match)",
                "steps": steps,
            }
        # 2) RAG path: answer from business documents, with citation.
        steps.append("RAG: searched business documents")
        results = self.index.search(question, top_k=1)
        if not results:
            return {
                "agent": "SupportAgent",
                "draft": "Sorry, I could not find an answer to this question in our documents. "
                "Please write your question in more detail and we will arrange a human reply.",
                "source": "No matching document",
                "steps": steps,
            }
        best = results[0]
        draft = f"According to our records: {best['text']}"
        return {
            "agent": "SupportAgent",
            "draft": draft,
            "source": f"Document: {best['source']}",
            "steps": steps,
        }


class DataAgent:
    """Extract structured fields from invoice/email text (regex version).

    This is intentionally rule-based in the starter: it is testable
    without an LLM, and it shows the validation idea clearly. A later
    version can add an LLM extractor and compare accuracy.
    """

    @staticmethod
    def extract(text: str) -> dict:
        amount = re.search(r"(?:Rs\.?|PKR)\s*([0-9,]+)", text, re.IGNORECASE)
        quantity = re.search(r"(\d+)\s*(?:pcs|pieces|items|shoes|shirt)", text, re.IGNORECASE)
        order = re.search(r"order\s*(?:no\.?|#)?\s*(\d+)", text, re.IGNORECASE)
        fields = {
            "amount": int(amount.group(1).replace(",", "")) if amount else None,
            "quantity": int(quantity.group(1)) if quantity else None,
            "order_id": order.group(1) if order else None,
            "raw_text": text,
        }
        missing = [k for k, v in fields.items() if v is None and k != "raw_text"]
        return {"fields": fields, "missing": missing, "valid": not missing}


class ReportingAgent:
    @staticmethod
    def daily_report() -> dict:
        orders = store.list_orders()
        total = sum(o["amount"] for o in orders)
        by_status: dict[str, int] = {}
        for o in orders:
            by_status[o["status"]] = by_status.get(o["status"], 0) + 1
        return {
            "total_orders": len(orders),
            "total_amount": total,
            "by_status": by_status,
            "pending_orders": [o for o in orders if o["status"] == "pending"],
        }


class Orchestrator:
    """Routes a task, runs the right agent, and queues the draft.

    Returns the same shape for every task so the dashboard can show
    the agent steps live: agent name, steps taken, draft, source,
    and the approval id the owner must approve.
    """

    def __init__(self, index: DocumentIndex):
        self.support = SupportAgent(index)
        self.data = DataAgent()
        self.reporting = ReportingAgent()

    def handle_question(self, question: str) -> dict:
        store.log("Orchestrator", "task_received", question)
        result = self.support.answer(question)
        approval_id = store.create_approval(
            task=question, draft=result["draft"], source=result["source"]
        )
        store.log(
            "Orchestrator",
            "draft_queued_for_approval",
            f"approval_id={approval_id}, agent={result['agent']}",
        )
        return {**result, "approval_id": approval_id, "status": "pending_approval"}

    def handle_invoice(self, text: str) -> dict:
        store.log("Orchestrator", "invoice_received", text[:120])
        result = self.data.extract(text)
        if not result["valid"]:
            draft = (
                "Some fields could not be extracted from the invoice: "
                + ", ".join(result["missing"])
                + ". Please send the complete details."
            )
            approval_id = store.create_approval(
                task="Invoice data entry", draft=draft, source="Invoice text"
            )
            return {
                "agent": "DataAgent",
                "fields": result["fields"],
                "missing": result["missing"],
                "draft": draft,
                "approval_id": approval_id,
                "status": "needs_human_input",
            }
        f = result["fields"]
        draft = (
            f"Invoice data is ready: order {f['order_id']}, "
            f"quantity {f['quantity']}, amount Rs {f['amount']}. "
            "It will be updated once approved."
        )
        approval_id = store.create_approval(
            task="Invoice data entry", draft=draft, source="Invoice text"
        )
        return {
            "agent": "DataAgent",
            "fields": f,
            "missing": [],
            "draft": draft,
            "approval_id": approval_id,
            "status": "pending_approval",
        }
