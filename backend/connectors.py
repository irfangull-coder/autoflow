"""Mock connectors for AutoFlow (proposal: tool abstraction).

Real email/WhatsApp/sheet accounts are out of scope for the demo, so
these connectors simulate the same interface with synthetic data.
A real connector later replaces these functions without changing
the agents: same input (text), same output shape (fields/task).

  mock_inbox()  -> a list of sample incoming emails/invoices
  mock_sheet_row(fields) -> the row that would be written to a sheet
"""
from .agents import DataAgent

SAMPLE_INBOX = [
    {
        "from": "ali@example.com",
        "subject": "New order",
        "text": "Order 1023, Ali ordered 2 shoes, Rs 4500",
    },
    {
        "from": "bilal@example.com",
        "subject": "Invoice",
        "text": "Order 1027, Bilal ordered 3 shirts, Rs 5400",
    },
    {
        "from": "ahmed@example.com",
        "subject": "Order query",
        "text": "Where is my order 1025?",
    },
]


def mock_inbox() -> list[dict]:
    """Return sample emails, each with DataAgent extraction attached."""
    out = []
    for mail in SAMPLE_INBOX:
        item = dict(mail)
        if "ordered" in mail["text"]:
            item["extracted"] = DataAgent.extract(mail["text"])
        out.append(item)
    return out


def mock_sheet_row(fields: dict) -> dict:
    """Simulate writing one row to a spreadsheet (no external call)."""
    return {
        "sheet": "AutoFlow Demo Sheet (mock)",
        "row_written": False,
        "reason": "Mock connector: row is prepared but not sent to a "
        "real spreadsheet in the demo. Approve the draft first.",
        "row": fields,
    }
