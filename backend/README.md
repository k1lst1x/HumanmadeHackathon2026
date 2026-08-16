# TextShop

An agent that runs a deck-making business inside iMessage. Customer texts a real number, the agent qualifies, prices, collects payment, builds in a sandbox, hires a human to verify, delivers — then reprices itself from what it learned.

## Run it now

```
pip install -r requirements.txt
python simulate.py          # dry-run, no API keys needed
uvicorn app:app --reload    # webhooks + dashboard on http://localhost:8000
```

Set `ANTHROPIC_API_KEY` to switch the reasoning layer from keyword fallbacks to real model calls. Without it everything still runs — `brain.py` degrades to heuristics rather than crashing.

`TEXTSHOP_DRY_RUN=1` (default) prints every integration call instead of making it. Flip to `0` once keys are wired.

## Superserve

Yes, you need a Superserve API key for the real sandbox path. Get it from the Superserve Console, then run:

```
export SUPERSERVE_API_KEY=ss_live_...
export TEXTSHOP_DRY_RUN=0
export TEXTSHOP_PUBLIC_BASE_URL=http://localhost:8000
```

`integrations.py` creates a sandbox from `SUPERSERVE_TEMPLATE` (`superserve/python-3.11` by default), uploads `generate.py` and `/work/deck.json`, installs `reportlab`, runs the deck generator, downloads `/work/deck.pdf` into `artifacts/`, then pauses the sandbox.

For Render, set `TEXTSHOP_PUBLIC_BASE_URL` to the deployed backend URL, for example:

```
TEXTSHOP_PUBLIC_BASE_URL=https://textshop-api.onrender.com
```

## Linq

Create a Linq webhook subscription for:

```
https://api.textshop.online/linq/webhook?version=2026-02-03
```

Subscribe at minimum to:

```
message.received
```

Store the returned signing secret in backend env:

```
LINQ_WEBHOOK_SECRET=whsec_...
```

You can create the subscription from this repo:

```
cd backend
python scripts/create_linq_webhook.py
```

Outbound messages use Linq Partner API v3. For replies to inbound messages,
TextShop sends to the existing Linq chat via `POST /v3/chats/{chatId}/messages`.
For legacy/direct phone sends, it uses `POST /v3/messages` and lets Linq choose
the best sending line. Set `LINQ_PIN_FROM=1` only if you explicitly need to send
from `LINQ_FROM_NUMBER`.

## Stripe / Agent Pay

Payment collection is a real Stripe Checkout Session. In hackathon/test mode,
use Stripe test keys so the production Render deployment can be tested with
Stripe test cards without moving real money:

```
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
TEXTSHOP_PUBLIC_BASE_URL=https://api.textshop.online
TEXTSHOP_DRY_RUN=0
```

Create a Stripe webhook endpoint that points to:

```
https://api.textshop.online/stripe/webhook
```

Subscribe to:

```
checkout.session.completed
```

After the customer accepts a quote, TextShop sends a Stripe Checkout link in
the Linq thread. After Stripe confirms `checkout.session.completed`, the job
advances from `COLLECT` to `BUILD`, revenue is posted to P&L once, and the
customer gets the confirmed payment message. The deck is generated only after
payment succeeds.

Use Stripe's standard test card in the hosted Checkout page:

```
4242 4242 4242 4242
any future expiry
any CVC
```

## Terac and Band fallback mode

`TERAC_API_KEY` and `BAND_API_KEY` can be present in production env without
crashing the customer flow. Until the real sponsor APIs are wired, TextShop logs
`fallback` calls, approves the review/verdict, and keeps the order moving to
delivery and Stripe Checkout.

## Database

You can connect the database before deployment. Create a Render Postgres
database in the same region as the backend service, then run:

```
backend/db/postgres_schema.sql
```

For local development, put the external Render Postgres connection string in
`backend/.env`:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE
```

Use Render's internal database URL from Render services in the same workspace
and region. Use the external database URL from your laptop, n8n, or any service
outside Render. Keep `DATABASE_URL` out of Git.

## File ownership — one person per file, no exceptions

| File | Owner | What it does |
|---|---|---|
| `orchestrator.py`, `pricing.py`, `store.py`, `brain.py` | Zafar | State machine, pricing memory, persistence, model calls |
| `integrations.py` → `Linq` | Person 2 | Number, card render + mutate, Agent Pay |
| `integrations.py` → `Superserve` | Person 3 | Sandbox, generation, pause/resume, artifact URL |
| `integrations.py` → `Band` | Person 4 | Three-agent room, blocking verdict |
| `app.py` | Zafar | Webhooks, P&L endpoint |

Person 2, 3, and 4 each replace one class in `integrations.py`. The `DRY_RUN` branch stays so the demo still runs if an integration dies.

## Env vars

```
LINQ_API_KEY=
LINQ_WEBHOOK_SECRET=
LINQ_FROM_NUMBER=
LINQ_PIN_FROM=0
SUPERSERVE_API_KEY=
SUPERSERVE_TEMPLATE=superserve/python-3.11
SUPERSERVE_TIMEOUT_SECONDS=900
SUPERSERVE_AUTO_DELETE_SECONDS=86400
TEXTSHOP_PUBLIC_BASE_URL=http://localhost:8000
DATABASE_URL=
TERAC_API_KEY=
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_CURRENCY=usd
BAND_API_KEY=
TEXTSHOP_DRY_RUN=0
TEXTSHOP_SEED_CENTS=5000
```

## State machine

```
INBOUND -> QUALIFY -> QUOTE -> NEGOTIATE -> COLLECT -> BUILD -> VERIFY -> DELIVER -> LEARN -> DONE
```

`advance()` runs transitions until a state needs new customer input, then returns. Every state is persisted, so the process can restart mid-job without losing a thread.

## The three decisions to point at during judging

1. **Repricing.** `pricing.quote_cents()` reads the last 8 outcomes. Acceptance above 70% raises price 15%, below 40% lowers it. Show quote #1 vs quote #10.
2. **Walking away.** In `NEGOTIATE`, if a counter would fall under 2x cost, the agent declines the job. Nobody told it to.
3. **Skipping verification.** In `VERIFY`, the agent refuses to pay for human review when the float is low or the job is too cheap to justify it. If a reviewer rejects the deck, the agent rebuilds once using review notes, then stops retrying to protect its budget.

## Band dependency (required for that track)

The room must have a real blocking edge or it doesn't qualify. Implemented in `on_quote`: the pricing agent can veto a quote and force it up. Person 4 must make `await_verdict` genuinely block — remove the room and the veto cannot happen.

## Render

Deploy `app.py` as a Render Workflow. Each state transition becomes a step, which gives retries and a run history you can put on screen.

## Known gaps before this is demo-ready

- Every integration is still a `DRY_RUN` stub. Persons 2, 3, and 4 replace their class.
- `Superserve.write_file` needs wiring — the sandbox must receive `/work/deck.json` and have `generate.py` plus reportlab installed.
- No retry or timeout on model calls. One slow response stalls a customer thread.
- Deck design is one fixed template. Fine at $25, not at $500.
- `TEXTSHOP_WEBHOOK_SECRET` is optional and unset by default. Set it before the number goes public.
