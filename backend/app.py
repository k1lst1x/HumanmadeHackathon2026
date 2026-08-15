import hmac
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import orchestrator
import store

app = FastAPI(title="TextShop")

SEED_FLOAT_CENTS = int(os.environ.get("TEXTSHOP_SEED_CENTS", "5000"))
WEBHOOK_SECRET = os.environ.get("TEXTSHOP_WEBHOOK_SECRET", "")
ARTIFACT_DIR = Path(
    os.environ.get("TEXTSHOP_ARTIFACT_DIR", Path(__file__).resolve().parent / "artifacts")
)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACT_DIR), name="artifacts")


@app.on_event("startup")
def startup():
    store.init()
    store.seed_float(SEED_FLOAT_CENTS)


def check_secret(provided):
    if not WEBHOOK_SECRET:
        return
    if not provided or not hmac.compare_digest(provided, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="bad webhook secret")


@app.post("/linq/webhook")
async def linq_webhook(request: Request, x_textshop_secret: str = Header(default="")):
    check_secret(x_textshop_secret)
    payload = await request.json()
    thread_id = payload.get("thread_id") or payload.get("from")
    text = payload.get("text") or payload.get("body") or ""
    event = payload.get("event")
    if not thread_id:
        return JSONResponse({"error": "missing thread_id"}, status_code=400)
    job = orchestrator.handle_message(thread_id, text, event=event)
    return {"job_id": job["id"] if job else None, "state": job["state"] if job else None}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, x_textshop_secret: str = Header(default="")):
    check_secret(x_textshop_secret)
    payload = await request.json()
    metadata = (payload.get("data", {}).get("object", {}) or {}).get("metadata", {}) or {}
    job_id = metadata.get("job_id")
    if not job_id:
        return JSONResponse({"error": "missing job_id"}, status_code=400)
    job = orchestrator.advance(job_id)
    return {"job_id": job_id, "state": job["state"] if job else None}


@app.get("/pnl")
def get_pnl():
    data = store.pnl()
    data["decisions"] = store.recent_decisions(25)
    data["outcomes"] = store.recent_outcomes(15)
    return data


@app.get("/health")
def health():
    return {"ok": True, "balance_cents": store.balance_cents()}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD


DASHBOARD = """
<!doctype html>
<meta charset="utf-8">
<title>TextShop</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:#0B0D12; color:#E7EAF0;
         font:15px/1.5 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif; padding:32px 40px; }
  h1 { font-size:20px; letter-spacing:.02em; margin:0 0 4px; }
  .sub { color:#7A8598; font-size:13px; margin-bottom:28px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-bottom:32px; }
  .card { background:#141821; border:1px solid #1F2531; border-radius:10px; padding:16px 18px; }
  .label { color:#7A8598; font-size:11px; text-transform:uppercase; letter-spacing:.09em; }
  .val { font-size:28px; font-weight:600; margin-top:6px; font-variant-numeric:tabular-nums; }
  .pos { color:#4ADE80; } .neg { color:#F87171; }
  h2 { font-size:12px; text-transform:uppercase; letter-spacing:.09em; color:#7A8598;
       margin:0 0 12px; font-weight:600; }
  ul { list-style:none; padding:0; margin:0; }
  li { padding:10px 0; border-bottom:1px solid #1A1F2A; display:flex; gap:12px; }
  .kind { color:#60A5FA; font-size:12px; min-width:150px; font-family:ui-monospace,monospace; }
  .cols { display:grid; grid-template-columns:1.4fr 1fr; gap:40px; }
  .price { font-variant-numeric:tabular-nums; }
  .ok { color:#4ADE80; } .no { color:#F87171; }
</style>
<h1>TextShop</h1>
<div class="sub">a company with no employees &middot; live</div>
<div class="grid" id="stats"></div>
<div class="cols">
  <div><h2>Decisions the agent made</h2><ul id="decisions"></ul></div>
  <div><h2>Pricing history</h2><ul id="outcomes"></ul></div>
</div>
<script>
const money = c => '$' + (c/100).toFixed(2);
async function tick() {
  const r = await fetch('/pnl');
  const d = await r.json();
  const margin = d.revenue_cents ?
    Math.round(100*(d.revenue_cents - d.verify_spend_cents - d.compute_spend_cents)/d.revenue_cents) : 0;
  document.getElementById('stats').innerHTML = [
    ['Revenue', money(d.revenue_cents), 'pos'],
    ['Float', money(d.balance_cents), ''],
    ['Paid to humans', money(d.verify_spend_cents), 'neg'],
    ['Gross margin', margin + '%', ''],
    ['Jobs done', d.jobs_done, ''],
    ['In flight', d.jobs_open, '']
  ].map(([l,v,c]) => `<div class="card"><div class="label">${l}</div>
     <div class="val ${c}">${v}</div></div>`).join('');
  document.getElementById('decisions').innerHTML = d.decisions.map(x =>
    `<li><span class="kind">${x.kind}</span><span>${x.summary}</span></li>`).join('');
  document.getElementById('outcomes').innerHTML = d.outcomes.map(x =>
    `<li><span class="price">${money(x.price_cents)}</span>
     <span class="${x.accepted ? 'ok' : 'no'}">${x.accepted ? 'accepted' : 'declined'}</span></li>`).join('');
}
tick(); setInterval(tick, 2000);
</script>
"""
