# IntelliReason — An AI-Powered Smart Reasoning System

IntelliReason takes a question that needs real reasoning and **doesn’t just answer it** — it
*plans*, *solves step-by-step with tools*, *verifies* the result, and *explains* exactly how it
got there. Think "show your work," enforced.

## How it works

1. **Decompose** — a Planner LLM breaks your problem into a few ordered, self-contained steps.
2. **Solve** — a LangChain ReAct agent solves each step, calling tools as needed.
3. **Verify** — a Verifier LLM checks every step and the final conclusion.
4. **Synthesize** — a Finalizer combines verified steps into one answer + a readable explanation.

Progress streams back to the UI as Server-Sent Events, so you watch the reasoning tree grow live.

## Stack

| Layer | Choice |
|---|---|
| LLM | Provider-agnostic — Groq / Google Gemini / OpenAI / OpenAI-compatible (config-swappable) |
| Agent framework | LangChain `create_agent` + ReAct |
| Reasoning | Chain-of-Thought decomposition + verify loop |
| Tools | Piston remote Python sandbox, SymPy symbolic math, knowledge-store retrieval |
| Backend | FastAPI |
| Frontend | React + Vite |
| Vector store | In-memory (dev) ↔ pgvector (prod) |
| Deploy | Docker locally; Render (backend) + Vercel/Netlify (frontend) |

## Quick start (backend)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# copy .env.example -> .env, fill GROQ_API_KEY (free: console.groq.com)
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs (API) and http://localhost:8000/api/health.

### Providers (pick one in `.env`)
| Provider | Free key | Model |
|---|---|---|
| `groq` | console.groq.com | `llama-3.3-70b-versatile` |
| `google` | aistudio.google.com | `gemini-2.0-flash` |
| `openai` | platform.openai.com | `gpt-4o-mini` |
| `openai_compatible` | Ollama etc. | your own |

## API

- `GET  /api/health` — status + active model
- `POST /api/stream-reason` — SSE stream: planning → steps → verification → done
- `POST /api/reason` — one-shot (non-stream) JSON result

### Piston sandbox (free, remote)
Code execution tool calls https://emkc.org/api/v2/piston — no local sandbox required.
Set `CODE_ENGINE=judge0` to use Judge0 instead (free tier). No key stored locally.

## Frontend

Requires Node 18+. See `frontend/README.md`.

## Deploy

- **Render blueprint** (`render.yaml`): deploy backend in one click; set `GROQ_API_KEY`.
- **Frontend**: `npm run build` → deploy `dist/` to Vercel or Netlify; set
  `VITE_API_URL` to your Render URL.
- **Docker**: `docker compose up` for a local full-stack environment.

## Tests

```powershell
cd backend; pytest -q
```

## Deeper reading

See `docs/DESIGN.md` for architecture, and `docs/TECHNOTES.md` for the reasoning-loop detail.