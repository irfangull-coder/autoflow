# AutoFlow — Starter Code (FYP Week 1–3)

**Project:** AutoFlow: A Multi-Agent AI Platform for Business Process Automation
**Student:** Muhammad Irfan — BS Artificial Intelligence, 7th Semester, The Islamia University of Bahawalpur

## Ye starter me kya hai? (Roman Urdu)

Ye Week 1–3 ka kaam karta hua prototype hai, sirf kagaz par design nahi:

1. **Orchestrator** — task ko samajh kar sahi agent ko deta hai
2. **Support Agent** — order status + RAG (business documents se jawab, source ke sath)
3. **Data Agent** — invoice/email text se amount, quantity aur order number nikaalta hai
4. **Reporting Agent** — orders se daily report banata hai
5. **Approval Queue** — koi message ya update bina human approval ke bahar nahi jata (yehi safety feature hai)
6. **Logs** — har agent action ka record
7. **Dashboard** — ek hi page par sawal, approval, invoice, report aur document upload

RAG is waqt simple token-overlap retrieval se chalta hai, taake bina kisi API key ke har laptop par chale. Baad me `backend/rag.py` me embeddings + ChromaDB/pgvector laga sakte ho, agents ko change kiye baghair, kyunki agents sirf `search()` ko call karte hain.

## Chalane ka tareeqa (Run)

```bash
cd autoflow
python3 -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Phir browser me kholo:

- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

## Demo script (Examiner ko ye 4 cheezein dikhana)

1. Sawal poocho: `mera order 1023 kahan hai?` → order status + approval queue me draft
2. Sawal poocho: `return policy kya hai?` → RAG jawab, source ke sath
3. Approval par **Approve** dabao → status approved ho jaye ga
4. Naya document upload karo (masalan nayi price list), phir usi bare me sawal poocho → jawab nayi document se aaye ga (live RAG proof)

## Tests

```bash
python3 -m pytest tests/ -q
# Agar pytest na ho to:
python3 tests/test_core.py
```

## Project structure

```
autoflow/
  backend/
    main.py        # FastAPI app + API endpoints + dashboard serve
    agents.py      # Orchestrator, SupportAgent, DataAgent, ReportingAgent
    rag.py         # Document index + search (baad me vector DB se replace hoga)
    store.py       # SQLite: orders, approvals, logs
  frontend/
    index.html     # Dashboard (vanilla HTML/JS, koi build step nahi)
  data/
    orders.json            # Synthetic orders (seed data)
    documents/*.txt        # Price list, return policy, FAQs (RAG source)
  tests/
    test_core.py   # RAG + DataAgent + Reporting ke basic tests
```

## Agle steps (Week 4 se)

- [ ] LLM call ko SupportAgent me optional banana (template draft ki jagah, wahi return shape rakh kar)
- [ ] `rag.py` me embeddings + ChromaDB/pgvector lagana
- [ ] Email aur Google Sheets ke real/mock connectors banana
- [ ] Scheduler Agent banana (daily report + reminders, waqt par)
- [ ] Evaluation script banana: manual vs single chatbot vs multi-agent, wahi test tasks par
- [ ] Har hafte GitHub par push karna aur progress note likhna

## Zaroori note

Demo me WhatsApp ka asli Business API nahi hai. Dashboard par message ka draft aur approval dikhta hai, jo ke demo ke liye theek hai. Thesis me ye saaf likhna hai ke WhatsApp connector mock hai, warna examiner ko dhoka lage ga.
