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
  "slides": [
    {
      "heading": "slide heading",
      "bullets": ["3 to 5 short bullets, under 12 words each"],
      "note": "one line of speaker guidance"
    }
  ]
}
Follow the standard investor arc: problem, solution, product, market, business model, traction,
competition, team, ask. Adapt to the requested slide count. Be specific and concrete.
Never invent fake metrics, customer names, or funding figures. Where a number belongs but is
unknown, write a bracketed placeholder like [ARR] so the founder fills it in."""


def generate_deck(scope):
    slide_count = scope.get("slide_count", 10)
    fallback = {
        "title": scope.get("company") or "Pitch Deck",
        "subtitle": scope.get("summary", ""),
        "slides": [
            {"heading": h, "bullets": ["[fill in]"], "note": ""}
            for h in [
                "Problem",
                "Solution",
                "Product",
                "Market",
                "Business Model",
                "Traction",
                "Competition",
                "Team",
                "The Ask",
            ][:slide_count]
        ],
    }
    user = (
        f"Brief: {scope.get('summary', '')}\n"
        f"Company: {scope.get('company', '')}\n"
        f"Audience: {scope.get('audience', '')}\n"
        f"Slides: {slide_count}"
    )
    return _json_call(DECK_SYSTEM, user, fallback, max_tokens=4000)
