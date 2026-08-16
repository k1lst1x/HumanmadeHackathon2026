import argparse
import os
import sys

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))

from integrations import Terac  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Create a real Terac review opportunity.")
    parser.add_argument(
        "--artifact-url",
        default="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        help="Public PDF URL for the reviewer to inspect.",
    )
    parser.add_argument(
        "--brief",
        default=(
            "Smoke test for TextShop. Review this PDF and return whether it is polished "
            "enough to deliver to a paying pitch-deck customer."
        ),
    )
    parser.add_argument("--budget-cents", type=int, default=300)
    args = parser.parse_args()

    task = Terac.request_review(args.artifact_url, args.brief, args.budget_cents)
    print(
        {
            "task_id": task.get("task_id"),
            "status": task.get("status"),
            "mode": task.get("mode"),
            "launched": task.get("launched"),
            "dashboard_url": task.get("dashboard_url"),
            "cost_cents": task.get("cost_cents"),
            "error": task.get("error"),
        }
    )


if __name__ == "__main__":
    main()
