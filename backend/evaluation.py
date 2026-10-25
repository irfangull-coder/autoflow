"""Honest, repeatable evaluation for AutoFlow.

Runs a fixed set of support and invoice cases through the real agents
(without creating approvals, so evaluation never pollutes the live
approval queue) and compares the full multi-agent system against a
single-agent baseline: RAG-only search with no order lookup and no
validation step.

Metrics reported:
  - task_success_rate: % of cases passing their expected check
  - data_entry_accuracy: % of invoice fields exactly correct
  - answer_accuracy: % of support answers passing their check
  - baseline_success_rate: same cases through the RAG-only baseline
  - avg_latency_ms: mean agent time per case

This is a demo-scale evaluation (18 cases: every seeded order plus
the policy/price/FAQ documents), not the 200-case set in the
proposal. The case list is explicit below so an examiner can
re-run it and see exactly what passed and what failed.
"""
import time
from pathlib import Path

from . import store
from .agents import DataAgent, SupportAgent
from .rag import DocumentIndex

BASE_DIR = Path(__file__).resolve().parent.parent

SUPPORT_CASES = [
    ("Where is my order 1023?", "dispatched", "Ali"),
    ("Where is my order 1024?", "delivered", "Fatima"),
    ("Where is my order 1025?", "pending", "Ahmed"),
    ("Where is my order 1026?", "dispatched", "Ayesha"),
    ("Where is my order 1027?", "pending", "Bilal"),
    ("Where is my order 1028?", "delivered", "Zainab"),
    ("What is the return policy?", "7 days", "return_policy"),
    ("How much are running shoes?", "2300", "price_list"),
    ("How long does delivery take?", "2 to 3 working days", "faqs"),
    ("What payment methods are available?", "cash on delivery", "faqs"),
    ("How can I change my order?", "before the order is dispatched", "faqs"),
    ("Where is my order 9999?", "no record", None),
]

INVOICE_CASES = [
    ("Order 1023, Ali ordered 2 shoes, Rs 4500",
     {"order_id": "1023", "quantity": 2, "amount": 4500}),
    ("Order 1024, Fatima ordered 1 shirt, Rs 1800",
     {"order_id": "1024", "quantity": 1, "amount": 1800}),
    ("Order 1025, Ahmed ordered 1 shoes, Rs 2300",
     {"order_id": "1025", "quantity": 1, "amount": 2300}),
    ("Order 1026, Ayesha ordered 1 bag, Rs 3200",
     {"order_id": "1026", "quantity": 1, "amount": 3200}),
    ("Order 1027, Bilal ordered 3 shirts, Rs 5400",
     {"order_id": "1027", "quantity": 3, "amount": 5400}),
    ("Order 1028, Zainab ordered 1 shoes, Rs 2500",
     {"order_id": "1028", "quantity": 1, "amount": 2500}),
]


def _load_index() -> DocumentIndex:
    index = DocumentIndex()
    for doc_path in sorted((BASE_DIR / "data" / "documents").glob("*.txt")):
        index.add_document(doc_path.stem, doc_path.read_text(encoding="utf-8"))
    return index


def _baseline_answer(index: DocumentIndex, question: str) -> str:
    """RAG-only baseline: no order lookup, no agent steps."""
    results = index.search(question, top_k=1)
    return results[0]["text"] if results else ""


def run_evaluation() -> dict:
    store.init_db()
    index = _load_index()
    agent = SupportAgent(index)
    support_results, baseline_results = [], []
    for question, expected, source_hint in SUPPORT_CASES:
        start = time.perf_counter()
        answer = agent.answer(question)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        draft = answer["draft"]
        # Order cases must name the right customer, not just contain
        # a status word that also appears in the FAQ text (e.g.
        # "dispatched" appears in "before the order is dispatched").
        # RAG cases must cite the right document.
        passed = expected.lower() in draft.lower()
        if source_hint and source_hint in ("return_policy", "price_list", "faqs"):
            passed = passed and source_hint in answer["source"]
        elif source_hint:
            passed = passed and source_hint.lower() in draft.lower()
        support_results.append({
            "question": question, "passed": passed,
            "draft": draft, "source": answer["source"],
            "latency_ms": latency_ms,
        })
        baseline_text = _baseline_answer(index, question)
        baseline_passed = expected.lower() in baseline_text.lower()
        if source_hint and source_hint not in ("return_policy", "price_list", "faqs"):
            baseline_passed = baseline_passed and source_hint.lower() in baseline_text.lower()
        baseline_results.append({
            "question": question,
            "passed": baseline_passed,
        })

    invoice_results, fields_total, fields_correct = [], 0, 0
    for text, expected in INVOICE_CASES:
        start = time.perf_counter()
        result = DataAgent.extract(text)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        fields = result["fields"]
        correct = sum(1 for k, v in expected.items() if fields.get(k) == v)
        fields_total += len(expected)
        fields_correct += correct
        invoice_results.append({
            "text": text, "fields": fields, "expected": expected,
            "fields_correct": correct, "fields_total": len(expected),
            "valid": result["valid"], "latency_ms": latency_ms,
        })

    all_cases = support_results + [
        {**r, "passed": r["fields_correct"] == r["fields_total"]}
        for r in invoice_results
    ]
    latencies = [r["latency_ms"] for r in all_cases]
    return {
        "cases_total": len(all_cases),
        "task_success_rate": round(
            sum(1 for r in all_cases if r["passed"]) / len(all_cases), 3),
        "answer_accuracy": round(
            sum(1 for r in support_results if r["passed"]) / len(support_results), 3),
        "data_entry_accuracy": round(fields_correct / fields_total, 3)
        if fields_total else 0,
        "baseline_success_rate": round(
            sum(1 for r in baseline_results if r["passed"]) / len(baseline_results), 3),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1)
        if latencies else 0,
        "support_results": support_results,
        "invoice_results": invoice_results,
        "baseline_results": baseline_results,
        "note": "Baseline is RAG-only (no order lookup, no validation). "
        "Evaluation creates no approvals and sends nothing.",
    }
