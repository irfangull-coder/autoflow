# AutoFlow — Complete Project (v1.0)

**Project:** AutoFlow: A Multi-Agent AI Platform for Business Process Automation
**Student:** Muhammad Irfan — BS Artificial Intelligence, 7th Semester, The Islamia University of Bahawalpur
**Note:** This is an assignment project (not a final year project).

**Live demo:** Frontend https://autoflow-demo-eight.vercel.app — Backend https://autoflow-api-fqns.onrender.com

## What is built

1. **Orchestrator** — routes tasks, plans steps, and verifies result shape
2. **Support Agent** — order status + RAG answers with source citations
3. **Data Agent** — extracts amount, quantity, and order number from invoice/email text, flags missing fields instead of guessing
4. **Reporting Agent** — daily report, pending orders, status breakdown, CSV download, chart
5. **Scheduler Agent** — daily report and payment-reminder jobs; every output is queued for approval, nothing is sent directly
6. **Approval Queue** — Approve / Reject / Edit Draft; no message or update leaves without human approval
7. **Tasks** — multi-step tasks with status tracking
8. **Documents** — upload, list, delete; uploaded documents persist in the database and survive restarts
9. **Logs** — audit trail for every agent action
10. **Evaluation** — fixed 18-case test set with measured results (see below)
11. **Mock connectors** — mock email inbox and mock sheet row (real accounts are out of scope)
12. **LLM hook** — `backend/llm.py` reports whether a real LLM provider is configured; the demo runs on template agents with no API key

RAG currently uses token-overlap retrieval so it runs with no API key. The interface (`DocumentIndex.search()`) is deliberately the same as a vector-DB version, so embeddings + ChromaDB/pgvector can replace the scoring later without changing the agents.

## Run locally

```bash
cd autoflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Then open:

- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

## Demo script

1. Ask: `Where is my order 1023?` → order status draft, queued for approval
2. Ask: `What is the return policy?` → RAG answer with source `return_policy`
3. Scheduler → Run Payment Reminders → drafts for pending orders, queued for approval
4. Evaluation → Run Evaluation → measured multi-agent vs RAG-only baseline results
5. Upload a new document, then ask about it → answer comes from the new document (live RAG proof)

## Evaluation (verified live, 2026-10-25)

18 cases: all 6 seeded orders (status + invoice extraction) plus return policy, price list, delivery, payment, and order-change questions.

- Multi-agent task success: 100%
- Answer accuracy: 100%
- Data-entry accuracy: 100%
- RAG-only baseline (no order lookup, no validation): 41.7% on support cases (5 of 12; it answers policy/price/FAQ questions but cannot answer any order-status question)
- Average latency: ~0.2 ms per case (template agents, no LLM call)

Run it anytime: `GET /api/evaluation` or the Evaluation section on the dashboard. Evaluation creates no approvals and sends nothing.

## Project structure

```
autoflow/
  backend/
    main.py        # FastAPI app, API endpoints, dashboard serving
    agents.py      # Orchestrator, Support, Data, Reporting, Scheduler agents
    rag.py         # Document index + search
    store.py       # SQLite: orders, approvals, logs, tasks, documents
    evaluation.py  # Fixed evaluation cases + baseline comparison
    connectors.py  # Mock email + sheet connectors
    llm.py         # Optional LLM provider status (disabled without a key)
  frontend/
    index.html     # Dashboard (vanilla HTML/JS, no build step)
    config.js      # Single place for the live backend URL
  data/
    orders.json            # Synthetic orders (seed data)
    documents/*.txt        # Price list, return policy, FAQs (RAG source)
  tests/
    test_core.py   # RAG, DataAgent, Scheduler, evaluation tests
```

## Tests

```bash
python3 -m pytest tests/ -q
# Or without pytest:
python3 tests/test_core.py
```

## Limitations (honest, by design)

- Demo data is synthetic; no real customer data is used.
- Render free tier sleeps after inactivity (first request can take 30–60s) and SQLite data resets on redeploy. Real persistence needs Postgres (Neon/Supabase) or a persistent disk.
- Real WhatsApp Business, real payments, a native mobile app, and a paid LLM API key are out of scope for this assignment demo. Messages are shown as approved drafts on the dashboard, not sent to real accounts.
- Scheduled jobs are run on demand from the dashboard; a persistent worker would be needed for true clock-based scheduling on a sleeping free tier.
