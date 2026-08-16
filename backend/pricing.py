import store

BASE_PRICE_CENTS = 1500
MIN_PRICE_CENTS = 900
MAX_PRICE_CENTS = 3500
STEP = 0.15
WINDOW = 8
MIN_SAMPLES = 3
VERIFY_COST_CENTS = 300
COMPUTE_COST_CENTS = 60


def floor_price_cents():
    return VERIFY_COST_CENTS + COMPUTE_COST_CENTS


def quote_cents(complexity=1.0):
    outcomes = store.recent_outcomes(WINDOW)
    if len(outcomes) < MIN_SAMPLES:
        price = BASE_PRICE_CENTS
        reason = "no pricing history, using base"
    else:
        accepted = sum(o["accepted"] for o in outcomes)
        rate = accepted / len(outcomes)
        last = outcomes[0]["price_cents"]
        if rate >= 0.7:
            price = int(last * (1 + STEP))
            reason = f"acceptance {rate:.0%} over last {len(outcomes)}, raising"
        elif rate <= 0.4:
            price = int(last * (1 - STEP))
            reason = f"acceptance {rate:.0%} over last {len(outcomes)}, lowering"
        else:
            price = last
            reason = f"acceptance {rate:.0%} over last {len(outcomes)}, holding"

    price = int(price * complexity)
    price = max(MIN_PRICE_CENTS, min(MAX_PRICE_CENTS, price))
    return price, reason


def margin_ok(price_cents, verify=True):
    cost = COMPUTE_COST_CENTS + (VERIFY_COST_CENTS if verify else 0)
    return price_cents >= cost * 2, cost


def should_verify(price_cents, balance_cents):
    if balance_cents < VERIFY_COST_CENTS * 2:
        return False, "float too low to pay for verification"
    if price_cents < VERIFY_COST_CENTS * 4:
        return False, "job too cheap to justify verification cost"
    return True, "margin supports human verification"
