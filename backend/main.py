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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import store
from .agents import Orchestrator, ReportingAgent
from .rag import DocumentIndex

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="AutoFlow Starter", version="0.2.0")

# --- CORS: Vercel frontend ko Render backend se baat karne dena -------
# Render par env var set karo, masalan:
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


class Question(BaseModel):
    question: str


class Invoice(BaseModel):
    text: str


class Document(BaseModel):
    title: str
    text: str


@app.get("/api/health")
def health():
    """Render health check + Vercel frontend ka connection test."""
    return {"ok": True, "service": "autoflow", "version": "0.2.0"}


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
    return found or {"error": "Order nahi mila"}


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
    store.log("Owner", "document_uploaded", f"{body.title}: {added} chunks")
    return {"ok": True, "title": body.title, "chunks_added": added}


app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")
