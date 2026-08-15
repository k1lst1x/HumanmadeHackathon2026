import json
import time

import brain
import pricing
import store
from integrations import Band, Linq, Stripe, Superserve, Terac

STATES = [
    "INBOUND",
    "QUALIFY",
    "QUOTE",
    "NEGOTIATE",
    "COLLECT",
    "BUILD",
    "VERIFY",
    "DELIVER",
    "LEARN",
    "DONE",
]

TERMINAL = {"DONE", "ABANDONED"}


def handle_message(thread_id, text, event=None, reply_to=None):
    job = store.active_job_for_thread(thread_id)
    if job is None:
        job_id = store.create_job(
            thread_id,
            "INBOUND",
            {"messages": [], "scope": None, "price_cents": None, "card_id": None},
        )
        job = store.get_job(job_id)
        store.log_decision("job_opened", f"opened job for {thread_id}", job_id=job_id)

    # Must set before advance() — Linq sends need an E.164 number, not chat UUID
    if reply_to:
        job["data"]["reply_to"] = reply_to

    job["data"].setdefault("messages", []).append(
        {"role": "customer", "text": text, "at": time.time(), "event": event}
    )
    store.save_job(job)
    return advance(job["id"])


def advance(job_id, max_steps=8):
    steps = 0
    while steps < max_steps:
        job = store.get_job(job_id)
        if job is None or job["state"] in TERMINAL:
            return job
        handler = HANDLERS.get(job["state"])
        if handler is None:
            return job
        next_state = handler(job)
        if next_state is None:
            return job
        job["state"] = next_state
        store.save_job(job)
        steps += 1
    return store.get_job(job_id)


def _recipient(job):
    thread_id = job["thread_id"]
    if str(thread_id).startswith("+") or "@" in str(thread_id):
        return job["data"].get("reply_to") or thread_id
    return thread_id


def _last_customer_text(job):
    for m in reversed(job["data"].get("messages", [])):
        if m["role"] == "customer":
            return (m["text"] or "").strip()
    return ""


def on_inbound(job):
    Linq.typing(_recipient(job), True)
    return "QUALIFY"


def on_qualify(job):
    text = _last_customer_text(job)
    scope = brain.extract_scope(text)
    job["data"]["scope"] = scope
    store.save_job(job)

    if not scope.get("clear"):
        Linq.send_text(
            _recipient(job),
            scope.get("question")
            or "Happy to help. What's the company, who's the audience, and how many slides?",
        )
        store.log_decision(
            "asked_clarification", "scope unclear, requested details", job_id=job["id"]
        )
        return None

    room = Band.open_room(job["id"])
    job["data"]["room_id"] = room["room_id"]
    store.save_job(job)
    Band.post(room["room_id"], "researcher", f"scoping: {scope['summary']}")
    return "QUOTE"


def on_quote(job):
    scope = job["data"]["scope"]
    price, reason = pricing.quote_cents(scope.get("complexity", 1.0))

    verdict = Band.await_verdict(job["data"]["room_id"], "pricing")
    if not verdict.get("approved"):
        price = max(price, pricing.floor_price_cents() * 2)
        store.log_decision(
            "price_vetoed",
            f"pricing agent blocked quote, raised to ${price / 100:.2f}",
            job_id=job["id"],
            detail=verdict.get("reason"),
        )

    job["data"]["price_cents"] = price
    card = Linq.send_quote_card(
        _recipient(job), job["id"], price, scope["summary"], scope.get("eta_minutes", 20)
    )
    job["data"]["card_id"] = card.get("card_id")
    store.save_job(job)
    store.log_decision(
        "quoted", f"quoted ${price / 100:.2f}", job_id=job["id"], detail=reason
    )
    return "NEGOTIATE"


def on_negotiate(job):
    text = _last_customer_text(job)
    price = job["data"]["price_cents"]
    scope = job["data"]["scope"]
    verdict = brain.classify_reply(text, price, scope.get("summary", ""))
    intent = verdict.get("intent", "unclear")

    if intent == "accept":
        _request_checkout(job)
        return "COLLECT"

    if intent == "change_scope":
        job["data"]["scope"] = brain.extract_scope(
            f"{scope.get('summary', '')}. Update: {verdict.get('new_scope') or text}"
        )
        store.save_job(job)
        store.log_decision("rescoped", "customer changed scope, requoting", job_id=job["id"])
        return "QUOTE"

    if intent in ("decline", "counter"):
        store.record_outcome(job["id"], price, accepted=False)
        asked = verdict.get("counter_price_cents")
        counter = int(asked) if asked else int(price * 0.85)
        ok, cost = pricing.margin_ok(counter)
        if ok:
            job["data"]["price_cents"] = counter
            store.save_job(job)
            Linq.update_card(
                _recipient(job),
                job["data"]["card_id"],
                "QUOTED",
                {"price": f"${counter / 100:.2f}"},
            )
            store.log_decision(
                "counter_offered",
                f"met customer at ${counter / 100:.2f}",
                job_id=job["id"],
            )
            return None
        Linq.send_text(
            _recipient(job),
            "That's below what this costs me to deliver. No hard feelings.",
        )
        store.log_decision(
            "walked_away",
            f"refused job under ${cost * 2 / 100:.2f} floor",
            job_id=job["id"],
        )
        return "DONE"

    if verdict.get("reply"):
        Linq.send_text(_recipient(job), verdict["reply"])
    return None


def on_build(job):
    Linq.update_card(_recipient(job), job["data"]["card_id"], "BUILDING")
    started = time.time()
    sandbox = Superserve.create_sandbox(job["id"])
    job["data"]["sandbox_id"] = sandbox["sandbox_id"]
    store.save_job(job)

    deck = brain.generate_deck(job["data"]["scope"])
    job["data"]["deck"] = deck
    store.save_job(job)
    Band.post(
        job["data"]["room_id"],
        "researcher",
        f"deck outline ready: {len(deck.get('slides', []))} slides",
    )
    Superserve.write_file(
        sandbox["sandbox_id"], "/work/deck.json", json.dumps(deck)
    )
    build = Superserve.run(sandbox["sandbox_id"], build_command(job["data"]["scope"]))
    if build.get("exit_code") != 0:
        error = build.get("stderr") or build.get("stdout") or "unknown generator failure"
        store.log_decision(
            "build_failed",
            "deck PDF generation failed",
            job_id=job["id"],
            detail=error[:500],
        )
        Linq.send_text(
            _recipient(job),
            "I hit a deck generation error after payment. I am retrying instead of sending a broken file.",
        )
        return None
    artifact = Superserve.export_artifact(sandbox["sandbox_id"], "/work/deck.pdf")
    Superserve.pause(sandbox["sandbox_id"])

    job["data"]["artifact_url"] = artifact["url"]
    job["data"]["build_seconds"] = time.time() - started
    store.save_job(job)
    store.post_ledger(
        "compute", -pricing.COMPUTE_COST_CENTS, job_id=job["id"], note="sandbox"
    )
    return "VERIFY"


def on_verify(job):
    price = job["data"]["price_cents"]
    verify, reason = pricing.should_verify(price, store.balance_cents())
    if not verify:
        job["data"]["verify_cost_cents"] = 0
        store.save_job(job)
        store.log_decision(
            "skipped_verification", reason, job_id=job["id"]
        )
        return "DELIVER"

    task = Terac.request_review(
        job["data"]["artifact_url"],
        f"check claims and flag anything embarrassing: {job['data']['scope']['summary']}",
        pricing.VERIFY_COST_CENTS,
    )
    result = Terac.poll_review(task["task_id"])
    cost = result.get("cost_cents", pricing.VERIFY_COST_CENTS)
    job["data"]["verify_cost_cents"] = cost
    job["data"]["verify_notes"] = result.get("notes")
    store.save_job(job)
    store.post_ledger("verify", -cost, job_id=job["id"], note="terac review")
    store.log_decision(
        "hired_human", f"paid ${cost / 100:.2f} for expert review", job_id=job["id"], detail=reason
    )

    if not result.get("approved"):
        Band.post(job["data"]["room_id"], "reviewer", result.get("notes", "revisions needed"))
        return "BUILD"
    return "DELIVER"


def on_deliver(job):
    Linq.update_card(
        _recipient(job),
        job["data"]["card_id"],
        "READY",
        {"artifact": job["data"]["artifact_url"]},
    )
    return "LEARN"


def on_collect(job):
    if not job["data"].get("checkout_id"):
        _request_checkout(job)
        return None

    result = Stripe.confirm_payment(job["data"].get("checkout_id"))
    if not result.get("paid"):
        job["data"]["last_payment_check"] = result
        store.save_job(job)
        return None
    price = job["data"]["price_cents"]
    job["data"]["payment"] = result
    store.save_job(job)
    if not store.has_ledger(job["id"], "revenue"):
        store.post_ledger("revenue", price, job_id=job["id"], note="stripe checkout")
    Linq.update_card(_recipient(job), job["data"]["card_id"], "CONFIRMED")
    return "BUILD"


def _request_checkout(job):
    checkout = Linq.request_payment(
        _recipient(job), job["data"]["card_id"], job["data"]["price_cents"], job["id"]
    )
    job["data"]["checkout"] = checkout
    job["data"]["checkout_id"] = checkout.get("checkout_id")
    store.save_job(job)

    if checkout.get("ok") and checkout.get("checkout_url"):
        store.log_decision(
            "checkout_created",
            f"created Stripe Checkout for ${job['data']['price_cents'] / 100:.2f}",
            job_id=job["id"],
            detail=checkout.get("checkout_id"),
        )
        return checkout

    store.log_decision(
        "checkout_failed",
        "Stripe Checkout was not created",
        job_id=job["id"],
        detail=str(checkout.get("error") or checkout),
    )
    return checkout


def on_learn(job):
    store.record_outcome(
        job["id"],
        job["data"]["price_cents"],
        accepted=True,
        build_seconds=job["data"].get("build_seconds"),
        verify_cost_cents=job["data"].get("verify_cost_cents"),
    )
    next_price, reason = pricing.quote_cents()
    store.log_decision(
        "repriced",
        f"next quote will be ${next_price / 100:.2f}",
        job_id=job["id"],
        detail=reason,
    )
    return "DONE"


def build_command(scope):
    return "python /work/generate.py --deck-json /work/deck.json --out /work/deck.pdf"


HANDLERS = {
    "INBOUND": on_inbound,
    "QUALIFY": on_qualify,
    "QUOTE": on_quote,
    "NEGOTIATE": on_negotiate,
    "BUILD": on_build,
    "VERIFY": on_verify,
    "DELIVER": on_deliver,
    "COLLECT": on_collect,
    "LEARN": on_learn,
}
