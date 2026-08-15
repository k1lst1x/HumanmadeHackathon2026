# Backend

FastAPI backend for the hackathon project.

## Stack

- Python 3.12
- FastAPI 0.141.x
- Uvicorn
- Pytest

## Run locally

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```
