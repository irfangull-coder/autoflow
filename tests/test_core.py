"""Basic tests for AutoFlow starter core logic (no FastAPI needed).

Run: python3 tests/test_core.py   OR   python3 -m pytest tests/ -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import DataAgent, ReportingAgent, SchedulerAgent
from backend.evaluation import run_evaluation
from backend.rag import DocumentIndex


def test_rag_finds_return_policy():
    index = DocumentIndex()
    index.add_document("return_policy", "Return policy: products can be returned within 7 days of delivery.")
    results = index.search("return policy kya hai?")
    assert results, "RAG ko return policy ka chunk milna chahiye"
    assert results[0]["source"] == "return_policy"


def test_data_agent_extracts_invoice():
    result = DataAgent.extract("Order 1023, Ali ne 2 shoes order kiye, Rs 4500")
    assert result["fields"]["amount"] == 4500
    assert result["fields"]["quantity"] == 2
    assert result["fields"]["order_id"] == "1023"
    assert result["valid"] is True


def test_data_agent_flags_missing_fields():
    result = DataAgent.extract("Hello, mujhe order chahiye")
    assert result["valid"] is False
    assert result["missing"], "Adhure invoice par missing fields batani chahiye"


def test_scheduler_payment_reminders_use_pending_orders():
    # Uses the seeded orders via store; run only as a shape check:
    # the function must return a list of dicts with a draft each.
    from backend import store

    store.init_db()
    reminders = SchedulerAgent.payment_reminders(min_days=0)
    assert isinstance(reminders, list)
    for r in reminders:
        assert r["draft"] and r["order_id"] and r["customer"]


def test_evaluation_runs_and_reports_metrics():
    result = run_evaluation()
    assert result["cases_total"] == 18
    assert 0 <= result["task_success_rate"] <= 1
    assert 0 <= result["baseline_success_rate"] <= 1
    assert result["avg_latency_ms"] >= 0


if __name__ == "__main__":
    test_rag_finds_return_policy()
    test_data_agent_extracts_invoice()
    test_data_agent_flags_missing_fields()
    test_scheduler_payment_reminders_use_pending_orders()
    test_evaluation_runs_and_reports_metrics()
    print("All core tests passed.")
