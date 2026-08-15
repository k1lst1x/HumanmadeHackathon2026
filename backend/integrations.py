import os
import time
import uuid

LINQ_API_KEY = os.environ.get("LINQ_API_KEY", "")
SUPERSERVE_API_KEY = os.environ.get("SUPERSERVE_API_KEY", "")
TERAC_API_KEY = os.environ.get("TERAC_API_KEY", "")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
BAND_API_KEY = os.environ.get("BAND_API_KEY", "")

DRY_RUN = os.environ.get("TEXTSHOP_DRY_RUN", "1") == "1"


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
    @staticmethod
    def create_sandbox(job_id):
        if DRY_RUN:
            return {"sandbox_id": f"sbx_{job_id}"}
        raise NotImplementedError("wire sandbox create")

    @staticmethod
    def run(sandbox_id, command):
        if DRY_RUN:
            print(f"[superserve:run] {sandbox_id}: {command[:80]}")
            return {"exit_code": 0, "stdout": "", "stderr": ""}
        raise NotImplementedError("wire sandbox exec")

    @staticmethod
    def write_file(sandbox_id, path, content):
        if DRY_RUN:
            print(f"[superserve:write] {sandbox_id}:{path} ({len(content)} bytes)")
            return {"ok": True}
        raise NotImplementedError("wire sandbox file write")

    @staticmethod
    def pause(sandbox_id):
        if DRY_RUN:
            print(f"[superserve:pause] {sandbox_id}")
            return {"ok": True}
        raise NotImplementedError("wire sandbox pause")

    @staticmethod
    def resume(sandbox_id):
        if DRY_RUN:
            print(f"[superserve:resume] {sandbox_id}")
            return {"ok": True}
        raise NotImplementedError("wire sandbox resume")

    @staticmethod
    def export_artifact(sandbox_id, path):
        if DRY_RUN:
            return {"url": f"https://artifacts.example/{sandbox_id}/deck.pdf"}
        raise NotImplementedError("wire artifact export to public URL")


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
