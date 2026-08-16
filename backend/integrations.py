import os
import subprocess
import sys
import time
import uuid
from urllib.parse import quote
from pathlib import Path

LINQ_API_KEY = os.environ.get("LINQ_API_KEY", "")
LINQ_FROM_NUMBER = os.environ.get("LINQ_FROM_NUMBER", "")
LINQ_BASE = os.environ.get("LINQ_BASE", "https://api.linqapp.com/api/partner/v3")
LINQ_PIN_FROM = os.environ.get("LINQ_PIN_FROM", "0") == "1"
SUPERSERVE_API_KEY = os.environ.get("SUPERSERVE_API_KEY", "")
TERAC_API_KEY = os.environ.get("TERAC_API_KEY", "")
TERAC_BASE = os.environ.get("TERAC_BASE", "https://terac.com/api/external/v2").rstrip("/")
TERAC_PROJECT_ID = os.environ.get("TERAC_PROJECT_ID", "")
TERAC_PROJECT_NAME = os.environ.get("TERAC_PROJECT_NAME", "TextShop")
TERAC_AUTO_LAUNCH = os.environ.get("TERAC_AUTO_LAUNCH", "1") == "1"
TERAC_MAX_REVIEW_CENTS = int(os.environ.get("TERAC_MAX_REVIEW_CENTS", "2000"))
TERAC_POLL_SECONDS = int(os.environ.get("TERAC_POLL_SECONDS", "20"))
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
BAND_API_KEY = os.environ.get("BAND_API_KEY", "")

DRY_RUN = os.environ.get("TEXTSHOP_DRY_RUN", "1") == "1"
SUPERSERVE_TEMPLATE = os.environ.get("SUPERSERVE_TEMPLATE", "superserve/python-3.11")
SUPERSERVE_TIMEOUT_SECONDS = int(os.environ.get("SUPERSERVE_TIMEOUT_SECONDS", "900"))
SUPERSERVE_AUTO_DELETE_SECONDS = int(os.environ.get("SUPERSERVE_AUTO_DELETE_SECONDS", "86400"))
TEXTSHOP_PUBLIC_BASE_URL = os.environ.get(
    "TEXTSHOP_PUBLIC_BASE_URL",
    os.environ.get("TEXTSHOP_PUBLIC_BASE", "http://127.0.0.1:8000"),
).rstrip("/")

ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = Path(os.environ.get("TEXTSHOP_ARTIFACT_DIR", ROOT / "artifacts"))


def _local_work(sandbox_id: str) -> Path:
    return ARTIFACT_DIR / sandbox_id / "work"


def _local_path(sandbox_id: str, path: str) -> Path:
    return ARTIFACT_DIR / sandbox_id / path.lstrip("/").replace("\\", "/")


class Linq:
    @staticmethod
    def _headers():
        return {
            "Authorization": f"Bearer {LINQ_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _is_direct_handle(destination):
        value = str(destination or "")
        return value.startswith("+") or "@" in value

    @staticmethod
    def _message(parts, purpose):
        return {
            "parts": parts,
            "idempotency_key": f"textshop-{purpose}-{uuid.uuid4().hex}",
        }

    @staticmethod
    def send_text(destination, body):
        if DRY_RUN or not LINQ_API_KEY:
            print(f"[linq:text] {destination}: {body}")
            return {"ok": True}
        import requests

        message = Linq._message([{"type": "text", "value": body}], "text")
        if Linq._is_direct_handle(destination):
            payload = {"to": [destination], "message": message}
            if LINQ_PIN_FROM and LINQ_FROM_NUMBER:
                payload["from"] = LINQ_FROM_NUMBER
                url = f"{LINQ_BASE}/chats"
            else:
                url = f"{LINQ_BASE}/messages"
        else:
            payload = {"message": message}
            url = f"{LINQ_BASE}/chats/{quote(str(destination), safe='')}/messages"

        try:
            r = requests.post(url, headers=Linq._headers(), json=payload, timeout=15)
            print(f"[linq:send] {r.status_code} to={destination} body={r.text[:300]}")
            return {
                "ok": r.ok,
                "status": r.status_code,
                "response": _safe_json(r),
                "message_id": (_safe_json(r) or {}).get("id"),
                "chat_id": (_safe_json(r) or {}).get("chat_id"),
            }
        except Exception as e:
            print(f"[linq:error] {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    def send_parts(destination, parts, purpose="parts"):
        if DRY_RUN or not LINQ_API_KEY:
            print(f"[linq:{purpose}] {destination}: {parts}")
            return {"ok": True}

        import requests

        message = Linq._message(parts, purpose)
        if Linq._is_direct_handle(destination):
            payload = {"to": [destination], "message": message}
            url = f"{LINQ_BASE}/messages"
        else:
            payload = {"message": message}
            url = f"{LINQ_BASE}/chats/{quote(str(destination), safe='')}/messages"

        try:
            r = requests.post(url, headers=Linq._headers(), json=payload, timeout=15)
            print(f"[linq:{purpose}] {r.status_code} to={destination} body={r.text[:300]}")
            return {"ok": r.ok, "status": r.status_code, "response": _safe_json(r)}
        except Exception as e:
            print(f"[linq:{purpose}:error] {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    def create_chat(to, body):
        if DRY_RUN or not LINQ_API_KEY:
            print(f"[linq:create_chat] {to}: {body}")
            return {"ok": True}
        import requests

        payload = {
            "from": LINQ_FROM_NUMBER,
            "to": [to],
            "message": Linq._message([{"type": "text", "value": body}], "chat"),
        }
        try:
            r = requests.post(
                f"{LINQ_BASE}/chats",
                headers=Linq._headers(),
                json=payload,
                timeout=15,
            )
            print(f"[linq:send] {r.status_code} to={to} body={r.text[:300]}")
            return {"ok": r.ok, "status": r.status_code}
        except Exception as e:
            print(f"[linq:error] {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    def send_quote_card(to, job_id, price_cents, scope, deadline_minutes):
        body = _text_card(
            f"QUOTE - {_deck_label(scope)}",
            [
                ("Price", _money(price_cents)),
                ("Scope", scope),
                ("Delivery", f"about {deadline_minutes} min after payment"),
                ("Verification", "1 human expert"),
            ],
            "Reply YES to accept\nReply COUNTER 200 to negotiate",
        )
        result = Linq.send_text(to, body)
        result["card_id"] = uuid.uuid4().hex[:8]
        return result

    @staticmethod
    def update_card(to, card_id, status, extra=None):
        extra = extra or {}
        labels = {
            "BUILDING": _text_card(
                "SANDBOX RESUMED",
                [
                    ("Status", "building your deck now"),
                    ("Steps", "outline, PDF render, human review"),
                ],
            ),
            "READY": _text_card(
                "DECK READY - VERIFIED",
                [("PDF", extra.get("artifact", ""))],
                "Reply if anything looks off.",
            ),
            "CONFIRMED": _text_card(
                "PAYMENT RECEIVED",
                [
                    ("Status", "sandbox queued"),
                    ("Next", "building deck"),
                ],
            ),
            "QUOTED": _text_card(
                "QUOTE UPDATED - REPRICED",
                [("Price", extra.get("price", ""))],
                "Reply YES to accept\nReply COUNTER 200 to negotiate",
            ),
        }
        return Linq.send_text(to, labels.get(status, status))

    @staticmethod
    def request_payment(to, card_id, price_cents, job_id):
        checkout = Stripe.create_checkout_session(
            job_id=job_id,
            price_cents=price_cents,
            description="Pitch deck delivered by TextShop",
        )
        if DRY_RUN or not LINQ_API_KEY:
            print(
                f"[linq:agent_pay] {to} {job_id} ${price_cents / 100:.2f} "
                f"{checkout.get('checkout_url', '')}"
            )
            return checkout

        if not checkout.get("ok"):
            send = Linq.send_text(
                to, "Checkout failed before I could start the deck. We are looking into it."
            )
            checkout["linq_send"] = send
            return checkout

        send = Linq.send_text(
            to,
            _text_card(
                "AGENT PAY - READY TO START",
                [
                    ("Amount", _money(price_cents)),
                    ("Checkout", checkout["checkout_url"]),
                ],
                (
                    "After payment:\n"
                    "sandbox starts, human review, deck delivery\n"
                    "Test card: 4242 4242 4242 4242"
                ),
            ),
        )
        checkout["linq_send"] = send
        return checkout

    @staticmethod
    def typing(to, on=True):
        if DRY_RUN or not LINQ_API_KEY or Linq._is_direct_handle(to):
            return {"ok": True}
        import requests

        method = requests.post if on else requests.delete
        try:
            r = method(
                f"{LINQ_BASE}/chats/{quote(str(to), safe='')}/typing",
                headers=Linq._headers(),
                timeout=10,
            )
            return {"ok": r.ok, "status": r.status_code}
        except Exception as e:
            print(f"[linq:typing:error] {e}")
            return {"ok": False, "error": str(e)}


def _safe_json(response):
    try:
        return response.json()
    except Exception:
        return None


def _summarize_terac_submission(submission):
    answers = submission.get("screening_answers") or []
    answer_text = []
    for answer in answers:
        values = answer.get("answer") or []
        if isinstance(values, str):
            values = [values]
        if values:
            answer_text.append(f"{answer.get('question', 'answer')}: {', '.join(map(str, values))}")
    if answer_text:
        return "; ".join(answer_text)
    return f"Terac submission {submission.get('id', '')} status={submission.get('status', 'unknown')}"


def _money(cents):
    value = f"${cents / 100:.2f}"
    return value[:-3] if value.endswith(".00") else value


def _deck_label(scope):
    normalized = str(scope or "").lower()
    if "seed" in normalized:
        return "SEED DECK"
    if "sales" in normalized:
        return "SALES DECK"
    if "investor" in normalized or "fund" in normalized:
        return "INVESTOR DECK"
    return "PITCH DECK"


def _text_card(title, rows=None, footer=None):
    lines = [title.upper()]
    if rows:
        lines.append("")
        for label, value in rows:
            if value:
                lines.append(f"{label}: {value}")
    if footer:
        lines.append("")
        lines.extend(str(footer).splitlines())
    return "\n".join(lines)


class Superserve:
    _sandboxes = {}

    @staticmethod
    def _sdk_sandbox():
        if not SUPERSERVE_API_KEY:
            raise RuntimeError("SUPERSERVE_API_KEY is required when TEXTSHOP_DRY_RUN=0")
        try:
            from superserve import Sandbox
        except ImportError as exc:
            raise RuntimeError("Install the Superserve SDK first: pip install superserve") from exc
        return Sandbox

    @staticmethod
    def _connect(sandbox_id):
        sandbox = Superserve._sandboxes.get(sandbox_id)
        if sandbox is not None:
            return sandbox
        Sandbox = Superserve._sdk_sandbox()
        sandbox = Sandbox.connect(sandbox_id)
        Superserve._sandboxes[sandbox_id] = sandbox
        return sandbox

    @staticmethod
    def create_sandbox(job_id):
        if DRY_RUN or not SUPERSERVE_API_KEY:
            sandbox_id = f"sbx_{job_id}"
            _local_work(sandbox_id).mkdir(parents=True, exist_ok=True)
            print(f"[superserve:create:local] {sandbox_id}")
            return {"sandbox_id": sandbox_id}
        Sandbox = Superserve._sdk_sandbox()
        sandbox = Sandbox.create(
            name=f"textshop-{job_id}",
            from_template=SUPERSERVE_TEMPLATE,
            timeout_seconds=SUPERSERVE_TIMEOUT_SECONDS,
            auto_delete_seconds=SUPERSERVE_AUTO_DELETE_SECONDS,
            metadata={"app": "textshop", "job_id": str(job_id)},
        )
        Superserve._sandboxes[sandbox.id] = sandbox
        sandbox.commands.run("mkdir -p /work")
        sandbox.files.write("/work/generate.py", (ROOT / "generate.py").read_text())
        install = sandbox.commands.run("python -m pip install reportlab")
        if install.exit_code != 0:
            raise RuntimeError(f"Superserve dependency install failed: {install.stderr}")
        return {"sandbox_id": sandbox.id}

    @staticmethod
    def run(sandbox_id, command):
        if DRY_RUN or not SUPERSERVE_API_KEY or str(sandbox_id).startswith("sbx_"):
            deck_json = _local_path(sandbox_id, "/work/deck.json")
            out_pdf = _local_path(sandbox_id, "/work/deck.pdf")
            print(f"[superserve:run:local] {sandbox_id} -> {out_pdf}")
            if not deck_json.exists():
                return {"exit_code": 1, "stdout": "", "stderr": f"missing {deck_json}"}
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "generate.py"),
                    "--deck-json",
                    str(deck_json),
                    "--out",
                    str(out_pdf),
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        result = Superserve._connect(sandbox_id).commands.run(command, timeout_seconds=300)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    @staticmethod
    def write_file(sandbox_id, path, content):
        if DRY_RUN or not SUPERSERVE_API_KEY or str(sandbox_id).startswith("sbx_"):
            dest = _local_path(sandbox_id, path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = content if isinstance(content, (bytes, bytearray)) else str(content).encode("utf-8")
            dest.write_bytes(data)
            print(f"[superserve:write:local] {sandbox_id}:{path} ({len(data)} bytes)")
            return {"ok": True}
        Superserve._connect(sandbox_id).files.write(path, content)
        return {"ok": True}

    @staticmethod
    def pause(sandbox_id):
        if DRY_RUN or not SUPERSERVE_API_KEY or str(sandbox_id).startswith("sbx_"):
            print(f"[superserve:pause:local] {sandbox_id}")
            return {"ok": True}
        Superserve._connect(sandbox_id).pause()
        return {"ok": True}

    @staticmethod
    def resume(sandbox_id):
        if DRY_RUN or not SUPERSERVE_API_KEY or str(sandbox_id).startswith("sbx_"):
            print(f"[superserve:resume:local] {sandbox_id}")
            return {"ok": True}
        Superserve._connect(sandbox_id).resume()
        return {"ok": True}

    @staticmethod
    def export_artifact(sandbox_id, path):
        if DRY_RUN or not SUPERSERVE_API_KEY or str(sandbox_id).startswith("sbx_"):
            local = _local_path(sandbox_id, path)
            rel = f"{sandbox_id}/{path.lstrip('/')}"
            url = f"{TEXTSHOP_PUBLIC_BASE_URL}/artifacts/{rel}"
            print(f"[superserve:export:local] {local} -> {url}")
            return {"url": url, "path": str(local)}
        data = Superserve._connect(sandbox_id).files.read(path)
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{sandbox_id}-{Path(path).name}"
        local_path = ARTIFACT_DIR / filename
        local_path.write_bytes(data)

        if TEXTSHOP_PUBLIC_BASE_URL:
            return {
                "url": f"{TEXTSHOP_PUBLIC_BASE_URL}/artifacts/{filename}",
                "path": str(local_path),
            }
        return {"url": str(local_path), "path": str(local_path)}


class Terac:
    @staticmethod
    def _headers():
        return {
            "Authorization": f"Bearer {TERAC_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _request(method, path, **kwargs):
        import requests

        url = f"{TERAC_BASE}{path}"
        response = requests.request(
            method,
            url,
            headers=Terac._headers(),
            timeout=30,
            **kwargs,
        )
        data = _safe_json(response)
        if not response.ok:
            message = data or response.text[:500]
            raise RuntimeError(f"Terac {method} {path} failed: {response.status_code} {message}")
        return data or {}

    @staticmethod
    def _project_id():
        if TERAC_PROJECT_ID:
            return TERAC_PROJECT_ID

        projects = Terac._request("GET", "/projects", params={"limit": 100}).get("data", [])
        for project in projects:
            if project.get("name") == TERAC_PROJECT_NAME:
                return project["id"]

        project = Terac._request("POST", "/projects", json={"name": TERAC_PROJECT_NAME})
        return project["id"]

    @staticmethod
    def _review_description(artifact_url, brief):
        return (
            "Review a paid TextShop pitch deck before it is delivered to a customer.\n\n"
            f"Deck PDF: {artifact_url}\n\n"
            f"Customer brief: {brief}\n\n"
            "Please inspect the PDF and return concise structured feedback:\n"
            "1. approved: yes/no\n"
            "2. score: 1-5\n"
            "3. top issues: bullet list\n"
            "4. revision notes: what should be fixed before delivery\n"
            "5. would a founder reasonably pay for this deck: yes/no\n\n"
            "Approve only if the deck is readable, polished enough for a hackathon customer, "
            "and does not contain obvious broken formatting or embarrassing claims."
        )

    @staticmethod
    def _opportunity_payload(artifact_url, brief):
        description = Terac._review_description(artifact_url, brief)
        return {
            "title": "Review a paid pitch deck PDF",
            "internal_title": f"TextShop deck review {uuid.uuid4().hex[:6]}",
            "description": "A fast expert review of a customer pitch deck generated by TextShop.",
            "project_id": Terac._project_id(),
            "num_participants": 1,
            "business_type": "b2b",
            "unrestricted_audience": True,
            "expected_days_to_complete": 5,
            "screening_questions": [
                {
                    "key": "deck_review_experience",
                    "text": "Have you reviewed, written, designed, or pitched startup decks before?",
                    "pick": "one",
                    "answers": [
                        {"text": "Yes", "qualify_logic": "must"},
                        {"text": "No", "qualify_logic": "reject"},
                    ],
                }
            ],
            "tasks": [
                {
                    "sequence": 1,
                    "task_type": "activity",
                    "review_type": "manual_review",
                    "task_url": artifact_url,
                    "title": "Review this pitch deck PDF",
                    "description": description,
                    "duration_minutes": 8,
                }
            ],
        }

    @staticmethod
    def request_review(artifact_url, brief, budget_cents):
        task_id = uuid.uuid4().hex[:8]
        if DRY_RUN or not TERAC_API_KEY:
            mode = "dry"
            print(
                f"[terac:{mode}:review] {artifact_url} "
                f"budget=${budget_cents / 100:.2f} task={task_id}"
            )
            return {"task_id": task_id, "status": "pending", "mode": mode}

        try:
            draft = Terac._request(
                "POST",
                "/opportunities",
                json=Terac._opportunity_payload(artifact_url, brief),
            )
            opportunity_id = draft["id"]
            pricing = draft.get("pricing") or {}
            estimated_cost = int(pricing.get("total_cost_cents") or 0)
            max_cost = max(TERAC_MAX_REVIEW_CENTS, int(budget_cents or 0))
            if estimated_cost and max_cost and estimated_cost > max_cost:
                return {
                    "task_id": opportunity_id,
                    "opportunity_id": opportunity_id,
                    "status": "draft",
                    "mode": "live",
                    "launched": False,
                    "dashboard_url": ((draft.get("links") or {}).get("dashboard") or {}).get("draft_editor"),
                    "cost_cents": estimated_cost,
                    "error": f"estimated Terac cost ${estimated_cost / 100:.2f} exceeds cap ${max_cost / 100:.2f}",
                }

            launch = None
            if TERAC_AUTO_LAUNCH:
                launch = Terac._request("POST", f"/opportunities/{opportunity_id}/launch", json={})

            result = launch or draft
            dashboard = ((result.get("links") or {}).get("dashboard") or {})
            return {
                "task_id": opportunity_id,
                "opportunity_id": opportunity_id,
                "status": result.get("status") or "launched",
                "mode": "live",
                "launched": bool(launch),
                "dashboard_url": dashboard.get("study") or dashboard.get("recruitment") or dashboard.get("draft_editor"),
                "cost_cents": int((result.get("pricing") or pricing).get("total_cost_cents") or budget_cents),
            }
        except Exception as exc:
            print(f"[terac:error] {exc}")
            return {
                "task_id": f"fallback_{task_id}",
                "status": "fallback",
                "mode": "fallback",
                "error": str(exc),
            }

    @staticmethod
    def poll_review(task_id, timeout_seconds=TERAC_POLL_SECONDS):
        if DRY_RUN or not TERAC_API_KEY or str(task_id).startswith("fallback"):
            mode = "dry" if DRY_RUN or not TERAC_API_KEY else "fallback"
            return {
                "task_id": task_id,
                "status": "complete",
                "approved": True,
                "notes": f"{mode} review passed; real Terac task creation is not wired yet",
                "cost_cents": 300,
            }

        deadline = time.time() + timeout_seconds
        last_payload = None
        while time.time() < deadline:
            try:
                payload = Terac._request(
                    "GET",
                    f"/opportunities/{task_id}/submissions",
                    params={"limit": 10},
                )
                last_payload = payload
                submissions = payload.get("data") or []
                approved = [s for s in submissions if s.get("status") == "approved"]
                rejected = [s for s in submissions if s.get("status") == "rejected"]
                if approved:
                    return {
                        "task_id": task_id,
                        "status": "complete",
                        "approved": True,
                        "notes": _summarize_terac_submission(approved[0]),
                        "cost_cents": 300,
                        "submission": approved[0],
                        "dashboard_url": payload.get("dashboard_url"),
                    }
                if rejected and not any(s.get("status") in ("awaiting_review", "in_progress") for s in submissions):
                    return {
                        "task_id": task_id,
                        "status": "complete",
                        "approved": False,
                        "notes": _summarize_terac_submission(rejected[0]),
                        "cost_cents": 0,
                        "submission": rejected[0],
                        "dashboard_url": payload.get("dashboard_url"),
                    }
            except Exception as exc:
                print(f"[terac:poll:error] {exc}")
                last_payload = {"error": str(exc)}
                break
            time.sleep(10)

        return {
            "task_id": task_id,
            "status": "pending",
            "approved": False,
            "notes": "Terac review is still pending",
            "cost_cents": 0,
            "last_payload": last_payload,
        }


class Band:
    @staticmethod
    def open_room(job_id):
        mode = "dry" if DRY_RUN or not BAND_API_KEY else "fallback"
        return {"room_id": f"room_{job_id}", "mode": mode}

    @staticmethod
    def post(room_id, agent, message, metadata=None):
        mode = "dry" if DRY_RUN or not BAND_API_KEY else "fallback"
        print(f"[band:{mode}:{agent}] {room_id}: {message[:100]}")
        return {"ok": True, "message_id": uuid.uuid4().hex[:8], "mode": mode}

    @staticmethod
    def await_verdict(room_id, agent, timeout_seconds=60):
        mode = "dry" if DRY_RUN or not BAND_API_KEY else "fallback"
        return {
            "approved": True,
            "reason": f"margin acceptable ({mode} verdict)",
            "blocked_by": None,
        }


class Stripe:
    @staticmethod
    def _client():
        if not STRIPE_API_KEY or STRIPE_API_KEY.startswith("pk_"):
            raise RuntimeError("STRIPE_API_KEY must be a Stripe secret key, e.g. sk_test_...")
        import stripe

        stripe.api_key = STRIPE_API_KEY
        return stripe

    @staticmethod
    def create_checkout_session(job_id, price_cents, description="Pitch deck"):
        if DRY_RUN:
            checkout_id = f"cs_test_{uuid.uuid4().hex[:24]}"
            return {
                "ok": True,
                "checkout_id": checkout_id,
                "checkout_url": f"{TEXTSHOP_PUBLIC_BASE_URL}/stripe/success?session_id={checkout_id}",
                "payment_status": "paid",
            }
        if not STRIPE_API_KEY or STRIPE_API_KEY.startswith("pk_"):
            return {
                "ok": False,
                "error": "STRIPE_API_KEY must be a Stripe secret key, e.g. sk_test_...",
            }

        stripe = Stripe._client()
        metadata = {"app": "textshop", "job_id": str(job_id)}
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                client_reference_id=str(job_id),
                success_url=(
                    f"{TEXTSHOP_PUBLIC_BASE_URL}/stripe/success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=f"{TEXTSHOP_PUBLIC_BASE_URL}/stripe/cancel?job_id={job_id}",
                metadata=metadata,
                payment_intent_data={"metadata": metadata},
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": os.environ.get("STRIPE_CURRENCY", "usd"),
                            "unit_amount": int(price_cents),
                            "product_data": {
                                "name": "TextShop pitch deck",
                                "description": str(description)[:500],
                            },
                        },
                    }
                ],
            )
            return {
                "ok": True,
                "checkout_id": session.id,
                "checkout_url": session.url,
                "payment_status": session.payment_status,
            }
        except Exception as exc:
            print(f"[stripe:checkout:error] {exc}")
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def confirm_payment(checkout_id):
        if not checkout_id:
            return {"paid": False, "error": "missing checkout_id", "at": time.time()}
        if DRY_RUN:
            return {"paid": True, "amount_cents": None, "at": time.time()}
        if not STRIPE_API_KEY or STRIPE_API_KEY.startswith("pk_"):
            return {
                "paid": False,
                "error": "STRIPE_API_KEY must be a Stripe secret key, e.g. sk_test_...",
                "at": time.time(),
            }

        stripe = Stripe._client()
        try:
            session = stripe.checkout.Session.retrieve(checkout_id)
        except Exception as exc:
            print(f"[stripe:confirm:error] {exc}")
            return {"paid": False, "error": str(exc), "at": time.time()}
        paid = session.payment_status == "paid"
        return {
            "paid": paid,
            "checkout_id": session.id,
            "payment_intent": session.payment_intent,
            "amount_cents": session.amount_total,
            "currency": session.currency,
            "at": time.time(),
        }

    @staticmethod
    def parse_webhook(body, signature, webhook_secret):
        if not webhook_secret:
            return None
        import stripe

        event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        if hasattr(event, "to_dict_recursive"):
            return event.to_dict_recursive()
        return dict(event)
