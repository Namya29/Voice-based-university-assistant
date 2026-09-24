# Multilingual Voice-Based University Assistant

Voice-first university assistant: speak a question in any supported language, it gets
transcribed and language-detected by Azure Speech, retrieved against official university
documents via Azure AI Search (RAG), answered by Microsoft Foundry's GPT-4.1-mini, and
spoken back in the same language.

## Folder structure

```
project/
├── backend/     FastAPI app (Python)
└── frontend/    React + Vite app (JavaScript)
```

## 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# now edit .env and fill in your real Azure/Foundry keys — never commit this file
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Verify it's running:

```bash
curl http://127.0.0.1:8001/api/health
```

Run backend tests (Azure calls are mocked, so no real keys needed):

```bash
pytest -q
```

## 2. Frontend setup

Open a **second terminal**, keep the backend running in the first:

```bash
cd frontend
npm install
cp .env.example .env      # only contains VITE_BACKEND_URL, no secrets
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`) in your browser.

Run frontend tests:

```bash
npm run test
```

## 3. Before a real demo

- Rotate any Azure/Foundry key that may have been shared anywhere insecurely; put only
  the new value in `backend/.env`.
- Create the Azure AI Search index (`university-docs`, vector field `content_vector`,
  1536 dimensions for `text-embedding-3-small`), then run:
  ```bash
  cd backend
  python -m app.ingest ./path/to/official_docs
  ```
  to embed and upload the university's official `.txt` documents.
- Confirm all endpoints respond with real credentials:
  ```bash
  curl http://127.0.0.1:8001/api/health
  curl http://127.0.0.1:8001/api/config/languages
  curl http://127.0.0.1:8001/api/speech/token
  curl -X POST http://127.0.0.1:8001/api/ask \
    -H "Content-Type: application/json" \
    -d '{"query":"When does the fall semester start?","language":"en-US"}'
  ```

## Security notes

- All Azure/Foundry secrets live only in `backend/.env`, which is git-ignored.
- The frontend never holds a long-lived Azure key; it gets a short-lived (10-minute)
  Speech token from the backend at `/api/speech/token` for browser-side microphone
  recognition.
- If `/api/ask` finds no relevant official document, it returns `verified: false` with a
  message saying the answer can't be confirmed, instead of guessing.
