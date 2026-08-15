import os
import sys

import requests


LINQ_API_KEY = os.environ.get("LINQ_API_KEY")
LINQ_BASE = os.environ.get("LINQ_BASE", "https://api.linqapp.com/api/partner/v3")
PUBLIC_BASE = (
    os.environ.get("TEXTSHOP_PUBLIC_BASE_URL")
    or os.environ.get("TEXTSHOP_PUBLIC_BASE")
    or "https://api.textshop.online"
).rstrip("/")
LINQ_FROM_NUMBER = os.environ.get("LINQ_FROM_NUMBER")


def main() -> int:
    if not LINQ_API_KEY:
        print("LINQ_API_KEY is required", file=sys.stderr)
        return 2

    target_url = f"{PUBLIC_BASE}/linq/webhook?version=2026-02-03"
    payload = {
        "target_url": target_url,
        "subscribed_events": [
            "message.received",
            "message.sent",
            "message.delivered",
            "message.failed",
        ],
    }
    if LINQ_FROM_NUMBER:
        payload["phone_numbers"] = [LINQ_FROM_NUMBER]

    response = requests.post(
        f"{LINQ_BASE}/webhook-subscriptions",
        headers={
            "Authorization": f"Bearer {LINQ_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=20,
    )

    print(f"POST {target_url}")
    print(f"Status: {response.status_code}")
    print(response.text)
    if response.ok:
        print("\nCopy signing_secret into Render as LINQ_WEBHOOK_SECRET.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
