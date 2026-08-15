import os
from pathlib import Path
import time
import uuid

LINQ_API_KEY = os.environ.get("LINQ_API_KEY", "")
SUPERSERVE_API_KEY = os.environ.get("SUPERSERVE_API_KEY", "")
TERAC_API_KEY = os.environ.get("TERAC_API_KEY", "")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
BAND_API_KEY = os.environ.get("BAND_API_KEY", "")

DRY_RUN = os.environ.get("TEXTSHOP_DRY_RUN", "1") == "1"
SUPERSERVE_TEMPLATE = os.environ.get("SUPERSERVE_TEMPLATE", "superserve/python-3.11")
SUPERSERVE_TIMEOUT_SECONDS = int(os.environ.get("SUPERSERVE_TIMEOUT_SECONDS", "900"))
SUPERSERVE_AUTO_DELETE_SECONDS = int(os.environ.get("SUPERSERVE_AUTO_DELETE_SECONDS", "86400"))
TEXTSHOP_PUBLIC_BASE_URL = os.environ.get("TEXTSHOP_PUBLIC_BASE_URL", "").rstrip("/")

ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = Path(os.environ.get("TEXTSHOP_ARTIFACT_DIR", ROOT / "artifacts"))


class Linq:
    @staticmethod
    def send_text(thread_id, body):
        if DRY_RUN:
            print(f"[linq:text] {thread_id}: {body}")
            return {"ok": True}
        raise NotImplementedError("wire POST /messages with LINQ_API_KEY")

    @staticmethod
    def send_quote_card(thread_id, job_id, price_cents, scope, deadline_minutes):
        payload = {
            "job_id": job_id,
            "status": "QUOTED",
            "price": f"${price_cents / 100:.2f}",
            "scope": scope,
            "eta": f"{deadline_minutes} min",
            "actions": ["accept", "change_scope", "decline"],
        }
        if DRY_RUN:
            print(f"[linq:card] {thread_id}: {payload}")
            return {"ok": True, "card_id": uuid.uuid4().hex[:8]}
        raise NotImplementedError("wire iMessage App card create")

    @staticmethod
    def update_card(thread_id, card_id, status, extra=None):
        if DRY_RUN:
            print(f"[linq:card_update] {thread_id} {card_id} -> {status} {extra or ''}")
            return {"ok": True}
        raise NotImplementedError("wire iMessage App card update")

    @staticmethod
    def request_payment(thread_id, card_id, price_cents, job_id):
        if DRY_RUN:
            print(f"[linq:agent_pay] {thread_id} {job_id} ${price_cents / 100:.2f}")
            return {"ok": True, "checkout_id": uuid.uuid4().hex[:8]}
        raise NotImplementedError("wire Agent Pay -> Apple Pay App Clip -> Stripe")

    @staticmethod
    def typing(thread_id, on=True):
        if DRY_RUN:
            return {"ok": True}
        raise NotImplementedError("wire typing indicator")


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
        if DRY_RUN:
            return {"sandbox_id": f"sbx_{job_id}"}
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
        if DRY_RUN:
            print(f"[superserve:run] {sandbox_id}: {command[:80]}")
            return {"exit_code": 0, "stdout": "", "stderr": ""}
        result = Superserve._connect(sandbox_id).commands.run(command, timeout_seconds=300)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    @staticmethod
    def write_file(sandbox_id, path, content):
        if DRY_RUN:
            print(f"[superserve:write] {sandbox_id}:{path} ({len(content)} bytes)")
            return {"ok": True}
        Superserve._connect(sandbox_id).files.write(path, content)
        return {"ok": True}

    @staticmethod
    def pause(sandbox_id):
        if DRY_RUN:
            print(f"[superserve:pause] {sandbox_id}")
            return {"ok": True}
        Superserve._connect(sandbox_id).pause()
        return {"ok": True}

    @staticmethod
    def resume(sandbox_id):
        if DRY_RUN:
            print(f"[superserve:resume] {sandbox_id}")
            return {"ok": True}
        Superserve._connect(sandbox_id).resume()
        return {"ok": True}

    @staticmethod
    def export_artifact(sandbox_id, path):
        if DRY_RUN:
            return {"url": f"https://artifacts.example/{sandbox_id}/deck.pdf"}
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
        if DRY_RUN:
            print(f"[terac:review] {artifact_url} budget=${budget_cents / 100:.2f}")
            return {"task_id": uuid.uuid4().hex[:8], "status": "pending"}
        raise NotImplementedError("wire Terac MCP expert task creation")

    @staticmethod
    def poll_review(task_id, timeout_seconds=300):
        if DRY_RUN:
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
        if DRY_RUN:
            return {"room_id": f"room_{job_id}"}
        raise NotImplementedError("wire Band room create")

    @staticmethod
    def post(room_id, agent, message, metadata=None):
        if DRY_RUN:
            print(f"[band:{agent}] {room_id}: {message[:100]}")
            return {"ok": True, "message_id": uuid.uuid4().hex[:8]}
        raise NotImplementedError("wire Band message post")

    @staticmethod
    def await_verdict(room_id, agent, timeout_seconds=60):
        if DRY_RUN:
            return {"approved": True, "reason": "margin acceptable", "blocked_by": None}
        raise NotImplementedError("wire Band blocking verdict from pricing agent")


class Stripe:
    @staticmethod
    def confirm_payment(checkout_id):
        if DRY_RUN:
            return {"paid": True, "amount_cents": None, "at": time.time()}
        raise NotImplementedError("wire Stripe payment intent lookup")
