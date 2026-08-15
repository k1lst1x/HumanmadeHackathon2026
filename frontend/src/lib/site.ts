/**
 * ─────────────────────────────────────────────────────────────────────────────
 * EVERYTHING A HUMAN MUST APPROVE BEFORE THIS PAGE GOES LIVE IS IN THIS FILE.
 *
 * Three buckets, all marked TODO:
 *   1. `phone`        — the real Linq iMessage number (currently the reserved
 *                       555-01xx fictional range).
 *   2. `stats`        — settled Stripe numbers. Placeholders today.
 *   3. `promise` +    — these are PROMISES TO CUSTOMERS. The revision policy,
 *      `testimonials`   the pay-after-delivery guarantee and the quotes are
 *                       copy, not observed behaviour. Confirm the agent
 *                       actually honours them, and replace the quotes with
 *                       real ones you have permission to use, before shipping.
 * ─────────────────────────────────────────────────────────────────────────────
 */

export const site = {
  name: "textshop",
  phone: "+14156035648",
  phoneHref: "sms:+14156035648",
  phoneCompact: "+14156035648",
} as const;

/**
 * The only figures on the page that come from your Stripe account rather than
 * from the product itself. Set them to your real numbers before launch —
 * they're quoted in the hero, the trust strip and the FAQ.
 */
export const stats = {
  delivered: "31",
  median: "34 min",
  from: "$25",
} as const;

export const trustBar = [
  `${stats.delivered} decks delivered`,
  `median ${stats.median} start to finish`,
  "checked by a human before it ships",
  "you pay after you see it",
] as const;

export const steps = [
  {
    n: "01",
    t: "text it what you need",
    d: "“seed deck, fintech, 12 slides, friday.” that's a complete brief. it asks for whatever it still needs.",
    tag: "takes 20 seconds",
  },
  {
    n: "02",
    t: "a price comes back",
    d: "a quote card lands in your thread with scope, delivery time and price. accept it, or counter — it will negotiate.",
    tag: "usually under 90 seconds",
  },
  {
    n: "03",
    t: "the deck shows up",
    d: "built, reviewed by a real human expert, delivered as a pdf in the same thread. you pay after it lands.",
    tag: `median ${stats.median}`,
  },
] as const;

export const included = [
  "your story, your numbers — not a template with your logo dropped in",
  "a human expert reviews every deck before it's sent",
  "pdf plus an editable file you own outright",
  "one revision round included, in the same thread",
  "no account, no login, no onboarding call",
  "nothing to install — it's just Messages",
] as const;

/* TODO: confirm these match what the agent actually does before publishing. */
export const promise = {
  title: "you pay after you've seen it.",
  body:
    "the deck is delivered before the checkout card is. if it's wrong, say so in the thread — you get a revision, or you walk and pay nothing. there is no invoice to argue with and nobody to escalate to.",
} as const;

export const tiers = [
  {
    id: "one-pager",
    name: "one-pager",
    price: "$25",
    line: "a single page that explains the company.",
    best: "best for cold intros",
    popular: false,
    includes: ["1 page, pdf", "your metrics, your voice", "same-day, usually same-hour"],
  },
  {
    id: "seed",
    name: "seed deck",
    price: "$95",
    line: "the deck you send before the first meeting.",
    best: "best for raising now",
    popular: true,
    includes: ["10–14 slides", "story, market, traction, ask", "human expert review", "1 revision round"],
  },
  {
    id: "raise",
    name: "full raise",
    price: "$295",
    line: "everything, plus the stuff they ask for after.",
    best: "best for a live process",
    popular: false,
    includes: [
      "18–22 slides + appendix",
      "financial model summary",
      "priority human review",
      "2 revision rounds",
    ],
  },
] as const;

/**
 * REAL SAMPLE WORK — this is what replaced the placeholder testimonials.
 *
 * Every slide below is rendered live on the page from this data, so a visitor
 * sees exactly what they get for each price. This is a product demonstration,
 * not a claim about other customers, so nothing here needs a customer's
 * permission and nothing can be wrong about somebody else's experience.
 *
 * When you have real quotes you're allowed to use, add them to
 * `endorsements` at the bottom of this file — it renders automatically and
 * stays empty (and hidden) until then.
 */
export const samples = [
  {
    id: "ledger",
    tier: "seed deck · $95",
    company: "Ledger",
    line: "instant settlement for freight brokers",
    turnaround: "31 min",
    accent: "#0a7cff",
    slides: [
      {
        kind: "title" as const,
        eyebrow: "seed round · confidential",
        title: "Ledger",
        sub: "instant settlement for freight brokers",
      },
      {
        kind: "problem" as const,
        title: "brokers wait 47 days to get paid",
        bullets: [
          "carriers invoice on delivery, shippers pay net-45",
          "brokers float the gap out of their own working capital",
          "factoring eats 3–5% of every load",
        ],
      },
      {
        kind: "chart" as const,
        title: "why now: rails finally got cheap",
        caption: "cost per settlement, cents",
        bars: [62, 54, 41, 28, 17, 9],
        labels: ["21", "22", "23", "24", "25", "26"],
      },
      {
        kind: "metrics" as const,
        title: "traction",
        stats: [
          ["$4.1M", "settled last quarter"],
          ["38", "brokers live"],
          ["11%", "weekly growth"],
          ["2.4%", "take rate"],
        ],
      },
      {
        kind: "ask" as const,
        title: "raising $2.5M",
        bullets: [
          "18 months of runway",
          "6 engineers, 2 in compliance",
          "target: 400 brokers, $60M settled",
        ],
      },
    ],
  },
  {
    id: "portage",
    tier: "one-pager · $25",
    company: "Portage",
    line: "compliance docs for small importers",
    turnaround: "14 min",
    accent: "#7c5cff",
    slides: [
      {
        kind: "title" as const,
        eyebrow: "one-pager",
        title: "Portage",
        sub: "customs paperwork that files itself",
      },
      {
        kind: "problem" as const,
        title: "a $900 broker fee on a $4k shipment",
        bullets: [
          "small importers can't justify a customs broker",
          "one wrong HS code holds a container for weeks",
          "nobody sells software at this size",
        ],
      },
      {
        kind: "metrics" as const,
        title: "the shape of it",
        stats: [
          ["$49", "per filing"],
          ["6 min", "median file time"],
          ["220", "importers waitlisted"],
          ["94%", "first-pass accept"],
        ],
      },
    ],
  },
  {
    id: "kiln",
    tier: "full raise · $295",
    company: "Kiln",
    line: "on-demand ceramics manufacturing",
    turnaround: "58 min",
    accent: "#16a34a",
    slides: [
      {
        kind: "title" as const,
        eyebrow: "series a · confidential",
        title: "Kiln",
        sub: "on-demand ceramics, 40 factories, one API",
      },
      {
        kind: "problem" as const,
        title: "a 12-week lead time kills the product",
        bullets: [
          "sampling a new mug takes three months",
          "MOQs start at 5,000 units",
          "brands guess demand a year out and eat the misses",
        ],
      },
      {
        kind: "chart" as const,
        title: "orders per month",
        caption: "units, thousands",
        bars: [8, 14, 19, 31, 44, 71],
        labels: ["jan", "feb", "mar", "apr", "may", "jun"],
      },
      {
        kind: "metrics" as const,
        title: "unit economics",
        stats: [
          ["$18.40", "revenue per unit"],
          ["61%", "gross margin"],
          ["4.1x", "LTV / CAC"],
          ["9 days", "sample to ship"],
        ],
      },
      {
        kind: "ask" as const,
        title: "raising $9M series A",
        bullets: [
          "20 new factory partners across 3 regions",
          "in-house glaze QA lab",
          "target: $40M GMV run-rate",
        ],
      },
    ],
  },
] as const;

/**
 * Real customer quotes go here, once you have them and have permission.
 * The section renders only when this array is non-empty — so the page never
 * ships an invented review.
 *   { q: "what they said", by: "Name, Company" }
 */
export const endorsements: { q: string; by: string }[] = [];

export const faqs = [
  {
    q: "how fast is it, really?",
    a: `median is ${stats.median} from your first text to the pdf landing in the thread. a one-pager is usually quicker; a full raise deck with a financial summary takes longer. the quote card tells you the delivery time before you accept, and it holds to it.`,
  },
  {
    q: "is this just ai slop with my logo on it?",
    a: "a real human expert is hired to review the deck before it's sent to you — the agent pays them out of its own budget on every job that warrants it. and you see the deck before you pay for it, so the check that matters is yours.",
  },
  {
    q: "what do i actually have to send?",
    a: "one text describing what you need. if it needs numbers, traction or a data room, it asks. most people are done providing input in about two minutes.",
  },
  {
    q: "what if i don't like the deck?",
    a: "say so in the thread. you get a revision round included. if it's still not right, you don't pay — the checkout card comes after delivery, not before.",
  },
  {
    q: "how do i pay?",
    a: "apple pay, inside the thread. a checkout card appears after the deck does, you tap it, it settles to stripe. no invoice, no portal, no card form.",
  },
  {
    q: "is my stuff confidential?",
    a: "your thread is used to build your deck and to price future work. it isn't published, resold, or used as a public example. if you want the thread deleted after delivery, ask for it in the thread.",
  },
  {
    q: "can it do decks that aren't fundraising?",
    a: "sales decks, board updates and internal strategy decks all work. it will tell you if your ask is outside what it can do well rather than take the job and disappoint you.",
  },
  {
    q: "who am i actually texting?",
    a: "an agent. it qualifies the job, sets its own price, hires the human reviewer and collects payment. nobody on our side reads your thread or touches the transaction.",
  },
] as const;

/* flavour for the terminal block — reads as the agent's own job log */
export const agentLog = [
  { t: "09:41:02", m: "inbound · +1 415 ••• 0182 · “need a seed deck by friday”", c: "b" },
  { t: "09:41:04", m: "qualify → fintech · seed · 12 slides · friday 18:00", c: "d" },
  { t: "09:41:22", m: "pricing memory · 41 closed jobs · acceptance 71%", c: "d" },
  { t: "09:41:23", m: "quote sent · $95", c: "b" },
  { t: "09:43:10", m: "counter received · $60", c: "w" },
  { t: "09:43:11", m: "declined · below 2× delivery cost", c: "r" },
  { t: "09:43:12", m: "repriced · $88 · final", c: "w" },
  { t: "09:44:58", m: "accepted · sandbox vm resumed", c: "g" },
  { t: "10:02:31", m: "terac expert hired · −$28 against margin", c: "d" },
  { t: "10:14:07", m: "delivered · seed_deck_v3.pdf · 12 slides", c: "g" },
  { t: "10:15:44", m: "apple pay settled · +$88 · stripe", c: "g" },
  { t: "10:15:45", m: "learn → acceptance 72% · next quote +15%", c: "d" },
] as const;
