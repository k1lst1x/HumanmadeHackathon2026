import base64
import hashlib
import hmac
import html
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import orchestrator
import store
from integrations import Stripe

app = FastAPI(title="TextShop")

SEED_FLOAT_CENTS = int(os.environ.get("TEXTSHOP_SEED_CENTS", "5000"))
WEBHOOK_SECRET = os.environ.get("TEXTSHOP_WEBHOOK_SECRET", "")
LINQ_WEBHOOK_SECRET = os.environ.get("LINQ_WEBHOOK_SECRET", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ARTIFACT_DIR = Path(
    os.environ.get("TEXTSHOP_ARTIFACT_DIR", Path(__file__).resolve().parent / "artifacts")
)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=str(ARTIFACT_DIR)), name="artifacts")


@app.on_event("startup")
def startup():
    store.init()
    store.seed_float(SEED_FLOAT_CENTS)


def check_secret(provided):
    if not WEBHOOK_SECRET:
        return
    if not provided or not hmac.compare_digest(provided, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="bad webhook secret")


def verify_linq_signature(secret, body, headers):
    if not secret:
        return True

    webhook_id = headers.get("webhook-id")
    timestamp = headers.get("webhook-timestamp")
    signature = headers.get("webhook-signature")
    if not webhook_id or not timestamp or not signature:
        return False

    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
        key = base64.b64decode(secret.removeprefix("whsec_"))
        signed = b".".join([webhook_id.encode(), timestamp.encode(), body])
        expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    except Exception:
        return False

    for part in signature.split():
        if not part.startswith("v1,"):
            continue
        if hmac.compare_digest(expected, part[3:]):
            return True
    return False


def extract_linq_message(payload):
    event_type = payload.get("event_type", "")
    data = payload.get("data", {}) or {}

    if not event_type and (payload.get("thread_id") or payload.get("from")):
        thread_id = payload.get("thread_id") or payload.get("from")
        return {
            "event_type": payload.get("event"),
            "thread_id": thread_id,
            "sender": payload.get("from") or thread_id,
            "text": payload.get("text") or payload.get("body") or "",
        }

    if event_type != "message.received":
        return {"ignored": event_type or "missing event_type"}

    if data.get("direction") and data.get("direction") != "inbound":
        return {"ignored": "outbound"}
    if data.get("is_from_me") is True:
        return {"ignored": "outbound"}

    chat = data.get("chat") or {}
    chat_id = chat.get("id") or data.get("chat_id")
    sender = (
        (data.get("sender_handle") or {}).get("handle")
        or (data.get("from_handle") or {}).get("handle")
        or data.get("from")
    )

    parts = data.get("parts")
    if parts is None:
        parts = (data.get("message") or {}).get("parts", [])

    text = " ".join(
        str(part.get("value", ""))
        for part in parts
        if part.get("type") == "text" and part.get("value")
    ).strip()

    return {
        "event_type": event_type,
        "thread_id": chat_id or sender,
        "sender": sender,
        "text": text,
    }


@app.post("/linq/webhook")
async def linq_webhook(request: Request, x_textshop_secret: str = Header(default="")):
    body = await request.body()
    linq_ok = LINQ_WEBHOOK_SECRET and verify_linq_signature(
        LINQ_WEBHOOK_SECRET, body, request.headers
    )
    legacy_ok = not WEBHOOK_SECRET or (
        x_textshop_secret and hmac.compare_digest(x_textshop_secret, WEBHOOK_SECRET)
    )
    if not linq_ok and not legacy_ok:
        raise HTTPException(status_code=401, detail="bad webhook signature")

    payload = json.loads(body)
    message = extract_linq_message(payload)
    if message.get("ignored"):
        return {"ignored": message["ignored"]}

    if not message.get("thread_id") or not message.get("text"):
        return {"ignored": "no text"}

    job = orchestrator.handle_message(
        message["thread_id"],
        message["text"],
        event=message.get("event_type"),
        reply_to=message.get("sender"),
    )
    return {"job_id": job["id"] if job else None, "state": job["state"] if job else None}


@app.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=""),
    x_textshop_secret: str = Header(default=""),
):
    body = await request.body()
    if STRIPE_WEBHOOK_SECRET:
        try:
            payload = Stripe.parse_webhook(body, stripe_signature, STRIPE_WEBHOOK_SECRET)
        except Exception:
            raise HTTPException(status_code=400, detail="bad stripe signature")
    else:
        check_secret(x_textshop_secret)
        payload = json.loads(body)

    event_type = payload.get("type")
    if event_type != "checkout.session.completed":
        return {"ignored": event_type}

    session = (payload.get("data", {}).get("object", {}) or {})
    metadata = session.get("metadata", {}) or {}
    job_id = metadata.get("job_id") or session.get("client_reference_id")
    if not job_id:
        return JSONResponse({"error": "missing job_id"}, status_code=400)
    job = orchestrator.advance(job_id)
    return {"job_id": job_id, "state": job["state"] if job else None}


@app.get("/stripe/success", response_class=HTMLResponse)
def stripe_success(session_id: str = ""):
    safe_session_id = html.escape(session_id)
    return f"""
<!doctype html>
<meta charset="utf-8">
<title>TextShop payment received</title>
<body style="font:16px/1.5 system-ui,sans-serif;padding:40px;max-width:680px;margin:auto">
  <h1>Payment received</h1>
  <p>Thanks. TextShop is starting your deck now and will update your message thread.</p>
  <p style="color:#666">Stripe session: {safe_session_id}</p>
</body>
"""


@app.get("/stripe/cancel", response_class=HTMLResponse)
def stripe_cancel(job_id: str = ""):
    safe_job_id = html.escape(job_id)
    return f"""
<!doctype html>
<meta charset="utf-8">
<title>TextShop payment canceled</title>
<body style="font:16px/1.5 system-ui,sans-serif;padding:40px;max-width:680px;margin:auto">
  <h1>Payment canceled</h1>
  <p>No charge was made. TextShop will wait to start until payment is complete.</p>
  <p style="color:#666">Job: {safe_job_id}</p>
</body>
"""


@app.get("/pnl")
def get_pnl():
    data = store.pnl()
    data["decisions"] = store.recent_decisions(25)
    data["outcomes"] = store.recent_outcomes(15)
    data["jobs"] = store.recent_jobs(20)
    data["ledger"] = store.recent_ledger(25)
    return data


@app.get("/health")
def health():
    return {
        "ok": True,
        "db_backend": store.backend_name(),
        "balance_cents": store.balance_cents(),
    }


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
  .sub { color:#9AA7BA; font-size:13px; margin-bottom:28px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  .pill { border:1px solid #2B3444; border-radius:999px; padding:3px 9px; color:#C7D2E5; background:#121722; font:11px ui-monospace,monospace; text-transform:uppercase; letter-spacing:.06em; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-bottom:32px; }
  .card { background:#141821; border:1px solid #1F2531; border-radius:10px; padding:16px 18px; }
  .label { color:#9AA7BA; font-size:11px; text-transform:uppercase; letter-spacing:.09em; }
  .val { font-size:28px; font-weight:600; margin-top:6px; font-variant-numeric:tabular-nums; }
  .pos { color:#4ADE80; } .neg { color:#F87171; }
  h2 { font-size:12px; text-transform:uppercase; letter-spacing:.09em; color:#9AA7BA;
       margin:0 0 12px; font-weight:600; }
  ul { list-style:none; padding:0; margin:0; }
  li { padding:10px 0; border-bottom:1px solid #1A1F2A; display:flex; gap:12px; align-items:flex-start; }
  .kind { color:#60A5FA; font-size:12px; min-width:150px; font-family:ui-monospace,monospace; }
  .cols { display:grid; grid-template-columns:1.35fr 1fr; gap:40px; margin-bottom:34px; }
  .section { min-width:0; }
  .price { font-variant-numeric:tabular-nums; }
  .ok { color:#4ADE80; } .no { color:#F87171; }
  .muted { color:#9AA7BA; }
  .mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }
  .job { display:grid; grid-template-columns:88px 92px 1fr 74px; gap:12px; }
  .state { color:#FBBF24; }
  .small { font-size:12px; }
  a { color:#93C5FD; }
  @media (max-width: 850px) {
    body { padding:22px; }
    .cols { grid-template-columns:1fr; }
    .job { grid-template-columns:1fr; gap:4px; }
  }
</style>
<h1>TextShop</h1>
<div class="sub">
  <span>a company with no employees &middot; live</span>
  <span class="pill" id="db">database</span>
</div>
<div class="grid" id="stats"></div>
<div class="cols">
  <div class="section"><h2>Orders in the database</h2><ul id="jobs"></ul></div>
  <div class="section"><h2>Ledger</h2><ul id="ledger"></ul></div>
</div>
<div class="cols">
  <div class="section"><h2>Decisions the agent made</h2><ul id="decisions"></ul></div>
  <div class="section"><h2>Pricing history</h2><ul id="outcomes"></ul></div>
</div>
<script>
const money = c => '$' + (c/100).toFixed(2);
const esc = v => String(v ?? '').replace(/[&<>"']/g, ch => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
}[ch]));
const ago = ts => {
  if (!ts) return '';
  const seconds = Math.max(0, Math.round(Date.now()/1000 - ts));
  if (seconds < 60) return seconds + 's ago';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return minutes + 'm ago';
  return Math.round(minutes / 60) + 'h ago';
};
async function tick() {
  const r = await fetch('/pnl');
  const d = await r.json();
  document.getElementById('db').textContent = esc(d.db_backend || 'database');
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
  document.getElementById('jobs').innerHTML = (d.jobs || []).map(x => {
    const artifact = x.artifact_url ? `<a href="${esc(x.artifact_url)}">PDF</a>` : '<span class="muted">no PDF yet</span>';
    return `<li class="job">
      <span class="mono">${esc(x.id)}</span>
      <span class="state mono">${esc(x.state)}</span>
      <span>${esc(x.scope || x.thread_id)}<br><span class="muted small">${esc(x.thread_id)} · ${ago(x.updated_at)}</span></span>
      <span>${artifact}</span>
    </li>`;
  }).join('');
  document.getElementById('ledger').innerHTML = (d.ledger || []).map(x =>
    `<li><span class="kind">${esc(x.kind)}</span><span class="${x.amount_cents >= 0 ? 'ok' : 'neg'}">${money(Math.abs(x.amount_cents))}</span><span class="muted">${esc(x.note || '')}</span></li>`
  ).join('');
  document.getElementById('decisions').innerHTML = d.decisions.map(x =>
    `<li><span class="kind">${esc(x.kind)}</span><span>${esc(x.summary)}</span></li>`).join('');
  document.getElementById('outcomes').innerHTML = d.outcomes.map(x =>
    `<li><span class="price">${money(x.price_cents)}</span>
     <span class="${x.accepted ? 'ok' : 'no'}">${x.accepted ? 'accepted' : 'declined'}</span></li>`).join('');
}
tick(); setInterval(tick, 2000);
</script>
"""
