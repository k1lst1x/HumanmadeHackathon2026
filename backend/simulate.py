import os

os.environ.setdefault("TEXTSHOP_DB", "sim.db")
os.environ.setdefault("TEXTSHOP_DRY_RUN", "1")

import orchestrator
import store

BRIEFS = [
    "I need a 10 slide seed deck for a dog walking marketplace targeting urban millennials",
    "Need a 12 slide pitch deck for a B2B invoicing tool aimed at seed investors next week",
    "Want an 8 slide deck for a coffee subscription startup for a demo day audience",
    "Need a deck for my AI note taking app, 10 slides, investor audience, clean design",
]


def run():
    if os.path.exists("sim.db"):
        os.remove("sim.db")
    store.init()
    store.seed_float(5000)

    replies = ["yes go ahead", "too much", "yes go ahead", "no thanks", "sounds good", "yes go ahead"]
    for i, brief in enumerate(BRIEFS):
        thread = f"+1555000{i:04d}"
        orchestrator.handle_message(thread, brief)
        orchestrator.handle_message(thread, replies[i % len(replies)])
        job = store.active_job_for_thread(thread)
        if job and job["state"] == "NEGOTIATE":
            orchestrator.handle_message(thread, "ok deal")
        print()

    p = store.pnl()
    print("=== P&L ===")
    print(f"balance      ${p['balance_cents'] / 100:.2f}")
    print(f"revenue      ${p['revenue_cents'] / 100:.2f}")
    print(f"verify spend ${p['verify_spend_cents'] / 100:.2f}")
    print(f"jobs done    {p['jobs_done']}")
    print()
    print("=== decisions ===")
    for d in reversed(store.recent_decisions(30)):
        print(f"  {d['kind']}: {d['summary']}")


if __name__ == "__main__":
    run()
