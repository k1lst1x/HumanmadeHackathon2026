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
        body = (
            f"${price_cents / 100:.2f} for: {scope}\n"
            f"Ready in about {deadline_minutes} min.\n"
            f"Reply YES to start, or name your price."
        )
        result = Linq.send_text(to, body)
        result["card_id"] = uuid.uuid4().hex[:8]
        return result

    @staticmethod
    def update_card(to, card_id, status, extra=None):
        extra = extra or {}
        labels = {
            "BUILDING": "On it. Building your deck now.",
            "READY": f"Done. Your deck: {extra.get('artifact', '')}".strip(),
            "CONFIRMED": "Payment received. Thanks for the business.",
            "QUOTED": f"Updated price: {extra.get('price', '')}",
        }
        return Linq.send_text(to, labels.get(status, status))

    @staticmethod
    def request_payment(to, card_id, price_cents, job_id):
        if DRY_RUN or not LINQ_API_KEY:
            print(f"[linq:agent_pay] {to} {job_id} ${price_cents / 100:.2f}")
            return {"ok": True, "checkout_id": uuid.uuid4().hex[:8]}
        Linq.send_text(to, f"Total due: ${price_cents / 100:.2f}")
        return {"ok": True, "checkout_id": uuid.uuid4().hex[:8]}

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
    def request_review(artifact_url, brief, budget_cents):
        if DRY_RUN or not TERAC_API_KEY:
            print(f"[terac:review] {artifact_url} budget=${budget_cents / 100:.2f}")
            return {"task_id": uuid.uuid4().hex[:8], "status": "pending"}
        raise NotImplementedError("wire Terac MCP expert task creation")

    @staticmethod
    def poll_review(task_id, timeout_seconds=300):
        if DRY_RUN or not TERAC_API_KEY:
            return {
                "task_id": task_id,
                "status": "complete",
                "approved": True,
                "notes": "no blocking issues",
                "cost_cents": 300,
            }
        raise NotImplementedError("wire Terac MCP task poll")


class Band:
    @staticmethod
    def open_room(job_id):
        if DRY_RUN or not BAND_API_KEY:
            return {"room_id": f"room_{job_id}"}
        raise NotImplementedError("wire Band room create")

    @staticmethod
    def post(room_id, agent, message, metadata=None):
        if DRY_RUN or not BAND_API_KEY:
            print(f"[band:{agent}] {room_id}: {message[:100]}")
            return {"ok": True, "message_id": uuid.uuid4().hex[:8]}
        raise NotImplementedError("wire Band message post")

    @staticmethod
    def await_verdict(room_id, agent, timeout_seconds=60):
        if DRY_RUN or not BAND_API_KEY:
            return {"approved": True, "reason": "margin acceptable", "blocked_by": None}
        raise NotImplementedError("wire Band blocking verdict from pricing agent")


class Stripe:
    @staticmethod
    def confirm_payment(checkout_id):
        # Stub until Agent Pay / Stripe webhook is wired — do not charge.
        if DRY_RUN or not STRIPE_API_KEY or STRIPE_API_KEY.startswith("pk_"):
            return {"paid": True, "amount_cents": None, "at": time.time()}
        raise NotImplementedError("wire Stripe payment intent lookup")
