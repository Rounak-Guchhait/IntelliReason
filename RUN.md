# RUN.md — Run & Deploy IntelliReason

One-line truth: **backend proven live end-to-end** (real Groq key, real LLM, real verification —
`12×12 → 144, verdict=correct`). Frontend builds to `dist/` with Node/Vite (Node not needed to
*run* the app — it's only used to build the UI; the UI can equally be served by the backend).

## 0. Prereqs
- python 3.11+  (tested: 3.14)
- node 18+ only if rebuilding the React UI (winget install OpenJS.NodeJS.LTS)
- one LLM key in `backend\.env` (see root `.env.example`)

## 1. Backend — run locally (one window)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1            # or: py -m venv .venv; .\.venv\Scripts\Activate.ps1  (first time)
pip install -r requirements.lock.txt
# edit .env: GROQ_API_KEY=gsk_...  (key needs model: openai/gpt-oss-120b works today)
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs → green. Health: http://localhost:8000/api/health
Quick self-test (no frontend needed):
```powershell
$b=@{question='What is 12*12? Verify step by step'}|ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/reason -Method Post -Body $b -ContentType 'application/json'
```

## 2. Frontend — only if you want the React UI at all (optional)
```powershell
cd frontend
npm install
npm run dev        # dev server on :5173 → talks to backend :8000
npm run build      # production → dist/ (Vite-hosted, or copy onto backend static/)
```

## 3. Full-stack local (backend serves the UI too — zero Node needed)
The Python backend can serve the built UI directly, so "full stack" is **one process**:
```powershell
# after: npm run build  →  copy frontend/dist into backend/static (or point at it)
uvicorn app.main:app --port 8000        # then just open http://localhost:8000
```
If you prefer no-Node: keep only FastAPI + a small vanilla HTML/JS page in backend/static.

## 4. Deploy
- Uvicorn one-command host: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Render sets $PORT).
- `deploy/render.yaml` — Render blueprint: backend service + optional static frontend service.
- `docker-compose.yml` + `backend/Dockerfile` — local container of the whole app.
- Env for prod: same `.env` keys as local (`GROQ_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`).
- Push to GitHub: `git init && git add -A && git commit -m "IntelliReason v0.1 — plan/solve/verify reasoning engine + UI" && git branch -M main && git remote add origin https://github.com/Rounak-Guchhait/IntelliReason.git && git push -u origin main`

## 5. Deeper config (backend/app/config.py + .env)
| Env | Default | Meaning |
|---|---|---|
| GROQ_API_KEY | — | Groq key (required) |
| LLM_PROVIDER | groq | groq / openai / google / openai_compatible |
| LLM_MODEL | openai/gpt-oss-120b | must exist on the provider |
| LLM_MAX_STEPS | 3 | planner splits into ≤N steps |
| VECTOR_STORE | memory | memory / pgvector |
| CODE_ENGINE | piston | piston / judge0 |

Tests: `cd backend; pytest -q`  → 9 passed.