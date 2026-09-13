IntelliReason
An AI-powered smart reasoning engine that plans, solves, verifies and explains — step by step, with tools, streaming live.

🎯 Live Demo
Try it now — no account needed beyond a free Groq key:

http://localhost:8000

Note: start the backend first (see Getting Started), then open the URL. Reasoning phases stream in real time.

Features
🗺️ Plan - Decomposes your question into a clear, ordered set of logical steps before solving anything
🧩 Solve - Each step is worked through with a ReAct agent that actually calls tools (Piston sandbox for Python, SymPy for symbolic math)
✅ Verify - Every step and the final conclusion are re-checked by a verifier model with an explicit verdict
🧠 Synthesize - Verified steps are woven into one readable, final explanation
⚡ Live Streaming - SSE stream shows planning → solving → verifying → synthesizing in real time, like watching it think
🔁 Provider-Agnostic - Same engine on Groq (default, free), OpenAI, Google Gemini, or any OpenAI-compatible API
🗄️ Knowledge Base - Retrieves relevant facts from an in-memory vector store (pgvector on Render)
🐳 Deploy Ready - Dockerfile, docker-compose, and Render blueprint included

Technology Stack
Python 3.12+
FastAPI - Async web framework with SSE streaming
LangChain 1.x - Agent orchestration (planner, solver, verifier agents)
Groq - Lightning-fast free LLM inference (llama-3.3-70b versatile, live-tested)
SymPy - Symbolic math tool
Piston - Remote sandbox for executing user code
Scikit-learn - Intent classification foundation
React + Vite - Interactive chat UI
Render / Docker - One-click deploy

Project Structure
IntelliReason/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + SSE routes
│   │   ├── api/               # /api/health, /api/reason, /api/stream-reason
│   │   ├── reasoning/         # engine.py: plan → solve → verify → synthesize
│   │   ├── agents/            # planner / solver / verifier LangGraph agents
│   │   ├── tools/             # code_exec (Piston), symbolic_math (SymPy), retrieval
│   │   ├── vectorstore/       # in-memory store (memory) + pgvector adapter
│   │   └── config.py          # single source of truth for .env
│   ├── requirements.txt       # + requirements.lock.txt (pinned)
│   ├── Dockerfile             # containerized backend
│   └── .env.example           # copy to .env, add your GROQ_API_KEY
├── frontend/
│   ├── src/                   # React app (App.jsx, components/, api/client.js)
│   ├── vite.config.js
│   └── package.json
├── render.yaml                # Render blueprint (backend + frontend)
├── docker-compose.yml
├── RUN.md                     # full run + deploy instructions
└── README.md

Getting Started
Prerequisites: Python 3.11+, git (Node.js only if you run the React UI).

Setup & Run
1. Clone the repository
  git clone <your-repo-url>
  cd IntelliReason

2. Start the backend
  cd backend
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  copy .env.example .env     # then add GROQ_API_KEY=gsk_... in .env
  uvicorn app.main:app --reload --port 8000

3. Verify it's alive
  Open http://localhost:8000/api/health  → {"status":"ok","app":"IntelliReason",...}

Usage Example
Open http://localhost:8000/docs and POST /api/reason with:

{ "question": "Solve x^2 - 5x + 6 = 0 step by step and verify the roots" }

You:  What is 12 × 12, worked out?
Steps:
  [1] Split: compute 12 × 12 and verify
  [2] Tool (python): 12 * 12  →  144
  [3] Verify: product correct (two-digit check)
Final answer: 144 · Verdict: correct ✓

How It Works
1. Decompose - The planner turns your question into ordered sub-steps.
2. Solve - A ReAct agent solves each step, calling Python (Piston) or SymPy where needed.
3. Verify - A verifier re-checks each step and the final conclusion, returning a verdict.
4. Synthesize - Steps and checks are combined into a single clear explanation.
The whole pipeline streams to the UI as server-sent events — planning → solving → verifying → synthesizing — so you watch each phase live.

Notes
- Uses Groq by default (free, no credit card). To switch providers, set LLM_PROVIDER=openai and add OPENAI_API_KEY in .env — no code changes.
- API key lives only in backend/.env, which is gitignored and never committed.
- Knowledge base stores facts in-memory for dev; swap to pgvector on Render via VECTOR_STORE=pgvector.
- 9 backend tests pass (pytest) and lint is clean (ruff).

Author
Rounak Guchhait
https://github.com/Rounak-Guchhait/IntelliReason