import json
import os
import re

MODEL = os.environ.get("TEXTSHOP_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = 2000

_client = None


def client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def _json_call(system, user, fallback, max_tokens=MAX_TOKENS):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return fallback
    try:
        resp = client().messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return json.loads(_strip_fences(text))
    except Exception as e:
        print(f"[brain:error] {e}")
        return fallback


def _strip_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return text


SCOPE_SYSTEM = """You are the intake agent for a business that sells pitch decks over text message.
Read the customer's message and decide whether you have enough to start work.
You need: what the company or product is, roughly who the deck is for, and how many slides.
Return ONLY a JSON object, no preamble, no markdown:
{
  "clear": true or false,
  "summary": "one line restating the job",
  "company": "what they are building",
  "audience": "who the deck is for",
  "slide_count": integer,
  "complexity": number between 0.8 and 1.6,
  "missing": ["field names you still need"],
  "question": "one short question to ask if unclear, else empty string"
}
complexity: 1.0 is a standard 10-slide investor deck. Raise it for heavy research, custom data, or unusual formats."""


def extract_scope(text):
    fallback = {
        "clear": len(text.split()) >= 8,
        "summary": text[:140],
        "company": "",
        "audience": "",
        "slide_count": 10,
        "complexity": 1.0,
        "missing": [],
        "question": "What's the company, who's the audience, and how many slides?",
    }
    result = _json_call(SCOPE_SYSTEM, text, fallback, max_tokens=600)
    result.setdefault("slide_count", 10)
    result["complexity"] = max(0.8, min(1.6, float(result.get("complexity", 1.0))))
    return result


REPLY_SYSTEM = """You are reading a customer's reply to a price quote sent over text message.
Classify their intent. Return ONLY a JSON object, no preamble, no markdown:
{
  "intent": "accept" | "decline" | "counter" | "change_scope" | "question" | "unclear",
  "counter_price_cents": integer or null,
  "new_scope": "string or empty",
  "reply": "one short message to send back, or empty string if no reply needed"
}
Use "counter" only when they name a different price or clearly ask for a discount.
Use "decline" when they are walking away.
Keep any reply under 25 words and conversational."""


def classify_reply(text, quoted_price_cents, scope_summary):
    lowered = text.lower()
    if any(w in lowered for w in ("accept", "yes", "deal", "go ahead", "ok", "sounds good")):
        fallback_intent = "accept"
    elif any(w in lowered for w in ("decline", "no thanks", "too much", "nevermind", "pass")):
        fallback_intent = "decline"
    else:
        fallback_intent = "unclear"

    fallback = {
        "intent": fallback_intent,
        "counter_price_cents": None,
        "new_scope": "",
        "reply": "",
    }
    user = (
        f"Job: {scope_summary}\n"
        f"We quoted: ${quoted_price_cents / 100:.2f}\n"
        f"Customer replied: {text}"
    )
    return _json_call(REPLY_SYSTEM, user, fallback, max_tokens=400)


DECK_SYSTEM = """You write pitch deck content. Given a brief, produce the full deck as structured data.
Return ONLY a JSON object, no preamble, no markdown:
{
  "title": "deck title",
  "subtitle": "one line positioning",
  "theme": "fintech_dark | studio_light | consumer_bright | enterprise_blue | climate_green | midnight_luxe",
  "visual_style": "2 to 5 words describing the design direction",
  "metrics": [
    {"value": "short number or proof point", "label": "what it means"}
  ],
  "slides": [
    {
      "type": "problem | solution | market | product | traction | business model | competition | team | ask",
      "layout": "split | grid | bullets | chart",
      "heading": "slide heading",
      "callout": "one memorable phrase or number",
      "bullets": ["3 to 5 concrete bullets, under 14 words each"],
      "note": "one line of speaker guidance for the founder"
    }
  ]
}
Make the deck feel designed: each slide needs a clear takeaway, not a generic label.
Pick a theme that matches the company category and audience. Use fintech_dark or
enterprise_blue for B2B, finance, security, and infrastructure; consumer_bright for consumer
apps and marketplaces; climate_green for climate, food, health, and sustainability;
midnight_luxe for premium products; studio_light for clean general-purpose decks.
Follow the investor arc: problem, solution, product, market, business model, traction,
competition, team, ask. Adapt to the requested slide count.
Use "chart" layout for market, traction, economics, or funnel slides. Use "grid" for product,
competition, and team. Use "split" for problem, solution, ask, and thesis slides.
Be specific to the customer's company and audience.
Never invent fake metrics, customer names, or funding figures. Where a number belongs but is
unknown, write a bracketed placeholder like [ARR] so the founder fills it in."""


def generate_deck(scope):
    slide_count = scope.get("slide_count", 10)
    company = scope.get("company") or "Pitch Deck"
    summary = scope.get("summary", "")
    audience = scope.get("audience", "")
    arc = [
        ("problem", "The pain is urgent and expensive", "Who struggles today and why current options fail"),
        ("solution", "A focused answer customers can understand", "What the company does in one sentence"),
        ("product", "The product turns the workflow into leverage", "What users actually do and get back"),
        ("market", "The wedge starts narrow, then expands", "Initial buyer, expansion path, and market logic"),
        ("business model", "Revenue follows the customer outcome", "Pricing, buyer, margin, and repeatability"),
        ("traction", "Early proof points make the story believable", "Use placeholders only where numbers are unknown"),
        ("competition", "The difference is speed, focus, or economics", "Why this wins against alternatives"),
        ("team", "The team has unfair context", "Why this group can execute"),
        ("ask", "The round buys one measurable milestone", "Amount, use of funds, and next proof point"),
    ][:slide_count]
    theme = _fallback_theme(f"{company} {summary} {audience}")
    fallback = {
        "title": company,
        "subtitle": summary or f"A sharper story for {audience or 'the next audience'}",
        "theme": theme,
        "visual_style": _fallback_style(theme),
        "metrics": [
            {"value": str(slide_count), "label": "slide investor narrative"},
            {"value": "1", "label": "clear wedge"},
            {"value": "next", "label": "milestone-ready ask"},
        ],
        "slides": [
            {
                "type": kind,
                "layout": ["split", "grid", "bullets", "chart"][i % 4],
                "heading": heading,
                "callout": kind.title(),
                "bullets": [
                    summary or "Customer brief goes here",
                    detail,
                    "Replace bracketed placeholders with founder data",
                ],
                "note": f"Make this slide specific to {company}.",
            }
            for i, (kind, heading, detail) in enumerate(arc)
        ],
    }
    user = (
        f"Brief: {scope.get('summary', '')}\n"
        f"Company: {scope.get('company', '')}\n"
        f"Audience: {scope.get('audience', '')}\n"
        f"Slides: {slide_count}"
    )
    return _json_call(DECK_SYSTEM, user, fallback, max_tokens=4000)


def _fallback_theme(text):
    lowered = str(text or "").lower()
    if any(w in lowered for w in ("fintech", "bank", "finance", "security", "infra", "api", "b2b")):
        return "fintech_dark"
    if any(w in lowered for w in ("climate", "energy", "health", "food", "sustain", "carbon")):
        return "climate_green"
    if any(w in lowered for w in ("luxury", "premium", "fashion", "creator", "studio")):
        return "midnight_luxe"
    if any(w in lowered for w in ("consumer", "marketplace", "social", "mobile", "app")):
        return "consumer_bright"
    if any(w in lowered for w in ("enterprise", "sales", "ops", "workflow", "saas")):
        return "enterprise_blue"
    return "studio_light"


def _fallback_style(theme):
    return {
        "fintech_dark": "precise premium dark",
        "studio_light": "clean editorial minimal",
        "consumer_bright": "bright app launch",
        "enterprise_blue": "crisp operator-grade",
        "climate_green": "calm organic growth",
        "midnight_luxe": "high-contrast premium",
    }.get(theme, "clean investor ready")
