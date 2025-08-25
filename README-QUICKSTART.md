## AutoQuest / RAGbot Pro — Quickstart Run Guide

This is a from-scratch guide to get the API running locally or with Docker, load documents, and make queries.

### Prerequisites
- Python 3.11+
- Windows PowerShell or a Unix-like shell
- Optional: Docker + Docker Compose (for containerized run)
- Optional (for GCC extractor): Google Chrome with remote debugging

### 1) Clone and set up environment
```powershell
cd C:\Users\ayans\Code
git clone <your-repo-url> AutoQuest
cd AutoQuest

# (Recommended) Create virtual environment
python -m venv .venv
. .venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

If you use Bash:
```bash
cd ~/Code
git clone <your-repo-url> AutoQuest
cd AutoQuest
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Configure environment
Copy the example env and adjust values:
```powershell
Copy-Item env.example .env
```

Key settings in `.env` you may want to tweak:
- `DEBUG=true` to enable interactive docs at `/docs` and `/redoc`
- `SECRET_KEY=<change-me>` for JWT signing
- `VECTOR_DB_TYPE=faiss|chroma|qdrant`
- `VECTOR_DB_PATH=./vector_db`
- `ENABLE_CACHE=true`
- `ENABLE_METRICS=true`

Note: If you forget to create `.env`, running `python run.py` once will copy `env.example` to `.env` and exit so you can edit it.

### 3) Start the API (local Python)
```powershell
python run.py --host 0.0.0.0 --port 8000 --debug
# or simply
python run.py
```

The server starts FastAPI (app is `autoquest.api.app:app`). If `DEBUG=true`, visit:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 4) Start the API (Docker or Compose)

Docker (single container):
```powershell
docker build -t autoquest:latest .
docker run -p 8000:8000 --name autoquest --rm autoquest:latest
```

Docker Compose (includes Redis, Qdrant, Prometheus, Grafana):
```powershell
docker compose up -d --build
# API:        http://localhost:8000
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000  (default admin/admin)
```

### 5) Get a token (demo JWT)
Issue a short-lived JWT for testing:
```powershell
$body = @{ role = "admin"; ttl_minutes = 60 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/auth/token -ContentType 'application/json' -Body $body
```
Response contains `access_token`. For curl:
```bash
curl -s -X POST http://localhost:8000/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"role":"admin","ttl_minutes":60}'
```

Use the token in subsequent calls: `Authorization: Bearer <token>`

### 6) Verify health
```bash
curl -s http://localhost:8000/health | jq .
```

### 7) Upload documents (build knowledge base)
Supported types: PDF, DOCX, TXT, MD, XLSX, CSV.

PowerShell example:
```powershell
$token = "<paste token here>"
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/upload `
  -Headers @{ Authorization = "Bearer $token" } `
  -Form @{ file = Get-Item .\sample.pdf }
```

curl example (Linux/macOS):
```bash
TOKEN=<paste token here>
curl -s -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F file=@sample.pdf
```

List documents:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/documents
```

### 8) Ask a question
```bash
curl -s -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What does the uploaded document say about topic X?",
    "top_k": 5,
    "similarity_threshold": 0.7,
    "question_type": "Factual"
  }'
```

Chat:
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role":"user","content":"Summarize key points"}],
    "include_context": true,
    "top_k": 4
  }'
```

Batch questions:
```bash
curl -s -X POST http://localhost:8000/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "batch_id": "demo1",
    "questions": [
      {"question":"Q1"},
      {"question":"Q2"}
    ]
  }'
```

### 9) Optional: GCC extractor (automated web data via Chrome)
Start Chrome with remote debugging enabled (Windows example):
```powershell
& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="C:\\temp\\chrome-debug"
```

Start extraction (uses `template.xlsx` if needed):
```bash
curl -s -X POST http://localhost:8000/gcc/start \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "input_file": "solutions.xlsx",
    "output_file": "solutions.xlsx",
    "template_file": "template.xlsx",
    "debug_port": 9222
  }'
```

Check status:
```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/gcc/status/<session_id>
```

Download outputs/logs:
```bash
curl -OJ -H "Authorization: Bearer $TOKEN" http://localhost:8000/gcc/download/solutions.xlsx
```

### 10) Monitoring
- Metrics endpoint (Prometheus): `GET /metrics`
- With Docker Compose: Prometheus at `http://localhost:9090`, Grafana at `http://localhost:3000` (admin/admin)

### 11) Troubleshooting
- 401 Unauthorized: Ensure you include `Authorization: Bearer <token>`
- 404 on `/docs`: Set `DEBUG=true` in `.env` or run `python run.py --debug`
- Vector DB errors: Set `VECTOR_DB_TYPE=faiss` for a zero-dependency default
- Port in use: Change `PORT` in `.env` or run `python run.py --port 8010`
- Missing packages: Run `pip install -r requirements.txt`
- Chrome not detected (GCC): Ensure Chrome is installed and remote debugging is enabled on the specified port

### 12) Useful endpoints
- `GET /health` — service health
- `GET /metrics` — Prometheus metrics
- `POST /auth/token` — get JWT for testing
- `POST /upload` — add a document
- `GET /documents` — list documents
- `POST /ask` — RAG answer
- `POST /chat` — chat with optional RAG context
- `POST /batch` — batch Q&A
- `POST /gcc/start`, `GET /gcc/status/{id}`, `GET /gcc/download/{file}` — optional GCC automation

### 13) File locations
- Vector DB: `./storage/vector_db`
- Logs: `./storage/logs`
- Temp uploads: `./storage/temp`
- Excel template: `./template.xlsx`


