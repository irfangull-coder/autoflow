"""AutoFlow starter API (FastAPI).

Run from the project root:
    pip install -r requirements.txt
    uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000  (dashboard)
API docs: http://127.0.0.1:8000/docs

The dashboard is a single static HTML file served from /frontend,
so the whole Week-1 demo works from one server, no build step.
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import store
from .agents import Orchestrator, ReportingAgent
from .evaluation import run_evaluation
from .rag import DocumentIndex

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="AutoFlow", version="0.3.0")

# --- CORS: Vercel frontend ko Render backend se baat karne dena -------
# Set the env var on Render, for example:
#   ALLOWED_ORIGINS=https://autoflow-demo.vercel.app,http://127.0.0.1:8000
# Agar env var na ho to local development ke liye localhost allow hai.
_allowed = os.environ.get("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in _allowed.split(",") if o.strip()] or [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load RAG documents on startup -------------------------------------
index = DocumentIndex()
for doc_path in sorted((BASE_DIR / "data" / "documents").glob("*.txt")):
    index.add_document(doc_path.stem, doc_path.read_text(encoding="utf-8"))

orchestrator = Orchestrator(index)


@app.on_event("startup")
def startup() -> None:
    store.init_db()
    # Reload user-uploaded documents saved in the database, so they
    # survive a restart (file documents are loaded at import time).
    for doc in store.list_documents():
        record = store.get_document(doc["title"])
        if record and record["title"] not in index.list_sources():
            index.add_document(record["title"], record["text"])


class Question(BaseModel):
    question: str


class Invoice(BaseModel):
    text: str


class Document(BaseModel):
    title: str
    text: str


class TaskIn(BaseModel):
    title: str
    kind: str = "question"
    payload: str = ""


class JobIn(BaseModel):
    kind: str
    min_days: int = 2


class DraftEdit(BaseModel):
    draft: str


@app.get("/api/health")
def health():
    """Render health check + Vercel frontend connection test."""
    return {"ok": True, "service": "autoflow", "version": "0.3.0"}


@app.get("/api/overview")
def overview():
    report = ReportingAgent.daily_report()
    pending = [a for a in store.list_approvals() if a["status"] == "pending"]
    return {
        "total_orders": report["total_orders"],
        "total_amount": report["total_amount"],
        "by_status": report["by_status"],
        "pending_orders": len(report["pending_orders"]),
        "pending_approvals": len(pending),
        "tasks": len(store.list_tasks()),
    }


@app.post("/api/tasks")
def create_task(body: TaskIn):
    task_id = store.create_task(body.title, body.kind)
    try:
        result = orchestrator.handle_task(body.title, body.kind, body.payload)
        status = "completed" if result.get("status") != "failed" else "failed"
    except Exception as exc:  # never leave a task stuck in "running"
        result = {"status": "failed", "error": str(exc)}
        status = "failed"
    import json as _json

    store.update_task(task_id, status, _json.dumps(result, default=str)[:2000])
    store.log("Orchestrator", "task_completed", f"task_id={task_id} status={status}")
    return {"task_id": task_id, "status": status, "result": result}


@app.get("/api/tasks")
def tasks():
    return store.list_tasks()


@app.post("/api/jobs/run")
def run_job(body: JobIn):
    return orchestrator.handle_scheduled(body.kind, min_days=body.min_days)


@app.get("/api/evaluation")
def evaluation():
    return run_evaluation()


@app.get("/config.js")
def config_js():
    """Local/Render full-stack run ke liye: index.html config.js ko
    root se mangta hai, Vercel par ye file waise hi static mile gi."""
    return FileResponse(BASE_DIR / "frontend" / "config.js")


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.post("/api/ask")
def ask(body: Question):
    return orchestrator.handle_question(body.question)


@app.post("/api/invoice")
def invoice(body: Invoice):
    return orchestrator.handle_invoice(body.text)


@app.get("/api/orders")
def orders():
    return store.list_orders()


@app.get("/api/orders/{order_id}")
def order(order_id: str):
    found = store.get_order(order_id)
    return found or {"error": "Order not found"}


@app.get("/api/approvals")
def approvals():
    return store.list_approvals()


@app.post("/api/approvals/{approval_id}/approve")
def approve(approval_id: int):
    ok = store.set_approval(approval_id, "approved")
    if ok:
        store.log("Owner", "approval", f"approval_id={approval_id} approved")
    return {"ok": ok, "status": "approved" if ok else "not_found"}


@app.post("/api/approvals/{approval_id}/reject")
def reject(approval_id: int):
    ok = store.set_approval(approval_id, "rejected")
    if ok:
        store.log("Owner", "approval", f"approval_id={approval_id} rejected")
    return {"ok": ok, "status": "rejected" if ok else "not_found"}


@app.get("/api/report")
def report():
    return ReportingAgent.daily_report()


@app.get("/api/logs")
def logs():
    return store.list_logs()


@app.post("/api/documents")
def add_document(body: Document):
    """Live RAG proof: upload a doc, then ask about it and the new
    answer comes from the new document."""
    added = index.add_document(body.title, body.text)
    store.save_document(body.title, body.text)
    store.log("Owner", "document_uploaded", f"{body.title}: {added} chunks")
    return {"ok": True, "title": body.title, "chunks_added": added}


@app.get("/api/documents")
def documents():
    built_in = sorted(
        {p.stem for p in (BASE_DIR / "data" / "documents").glob("*.txt")}
    )
    uploaded = store.list_documents()
    return {
        "built_in": built_in,
        "uploaded": uploaded,
        "indexed_sources": index.list_sources(),
    }


@app.delete("/api/documents/{title}")
def delete_document(title: str):
    removed_chunks = index.remove_source(title)
    removed_record = store.delete_document(title)
    store.log("Owner", "document_deleted", f"{title}: {removed_chunks} chunks")
    return {"ok": removed_chunks > 0 or removed_record,
            "title": title, "chunks_removed": removed_chunks}


@app.patch("/api/approvals/{approval_id}")
def edit_approval(approval_id: int, body: DraftEdit):
    ok = store.update_approval_draft(approval_id, body.draft)
    if ok:
        store.log("Owner", "approval_edited", f"approval_id={approval_id}")
    return {"ok": ok, "status": "pending" if ok else "not_found_or_not_pending"}


@app.get("/api/report.csv")
def report_csv():
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "customer", "product", "quantity", "amount", "status", "date"])
    for o in store.list_orders():
        writer.writerow([o["id"], o["customer"], o["product"],
                         o["quantity"], o["amount"], o["status"], o["date"]])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=autoflow_report.csv"})


app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")
