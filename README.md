# HumanmadeHackathon2026

The World's First Zero Human Company Hackathon.

## Project layout

```text
backend/   Python 3.12 + FastAPI API
frontend/  React + Vite + TypeScript app
```

## Version choices

- Backend runtime: Python 3.12.
- Backend framework: FastAPI 0.141.x. FastAPI does not have an LTS channel, so we keep a narrow minor range.
- Frontend runtime: Node.js 24 LTS.
- Frontend framework: React 19.2.x. React does not have an LTS channel; we use the current stable major.
- Frontend tooling: Vite 8.2.x + TypeScript 7.0.x.

## Run backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

## Run frontend

Use Node 24 first:

```bash
nvm use
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server: http://localhost:5173
Backend API: http://localhost:8000
