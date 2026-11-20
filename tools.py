"""Royal Table tools: account scoring, invite list and spend request.

Pure functions with no Streamlit, boto3 or global state, so they can be unit tested and
called by the Bedrock agent through the dispatcher in app.py. Every number the agent
reports comes from here. Rules are documented in README.md (Scoring rules) and in
.kiro/specs/target-curator-agent/requirements.md.

Public tools:
    score_accounts(rows)                                  -> list of scored accounts
    build_invite_list(scored, rows, room_size=40)         -> invite list and executive count
    draft_spend_request(budget, invite_list, justification) -> request, always Pending Approval
"""

import csv

# Fixed weights (requirement 3). Dict order is the tie-break order for reasons.
WEIGHTS = {
    "local_decision_authority": 20,
    "offering_fit": 25,
    "trigger_signals": 20,
    "deal_size_fit": 15,
    "relationship_warmth": 10,
    "persona_confidence": 10,
}

# Executive-language phrases for the one sentence reason, keyed by signal and value.
PHRASES = {
    "offering_fit": {"High": "our offering maps to a stated priority",
                     "Medium": "our offering is a partial fit", "Low": "our offering is a weak fit"},
    "deal_size_fit": {"High": "the deal size is in our sweet spot",
                      "Medium": "the deal size is workable", "Low": "the deal size is below target"},
    "relationship_warmth": {"Warm": "we have a warm executive relationship",
                            "Known": "the executive team already knows us",
                            "Cold": "there is no executive relationship yet"},
    "persona_confidence": {"High": "the right executives are confirmed",
                           "Medium": "the right executives are likely identified",
                           "Low": "the right executives are not yet confirmed"},
}

# Trigger keyword -> reason code an executive recognises. First match wins.
TRIGGER_CODES = [
    ("exam", "Regulator deadline"),
    ("regulatory", "Regulator deadline"),
    ("ai initiative", "AI mandate from the top"),
    ("migration", "Modernization budget in motion"),
    ("modernization", "Modernization budget in motion"),
    ("governance", "Data governance under scrutiny"),
    ("funding", "Fresh capital to deploy"),
    ("hiring", "Building a data team now"),
    ("launch", "Launch date on the calendar"),
]

# Invite accounts at or above this score are flagged Highly recommended (requirement 13).
HIGHLY_RECOMMENDED_MIN = 90

C_SUITE = ("CEO", "CFO", "CIO", "CTO", "CDO", "COO", "CISO", "CRO")

AUTHORITY = {"Yes": 3, "Partial": 2, "No": 0}
LEVEL = {"High": 3, "Medium": 2, "Low": 1}
WARMTH = {"Warm": 3, "Known": 2, "Cold": 0}
CURRENT_TIER = {"Tier 1": "Invite", "Tier 2": "Nurture", "Tier 3": "Deprioritize"}
TIER_RANK = {"Invite": 0, "Nurture": 1, "Deprioritize": 2}


def load_accounts(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def split_items(value):
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def points(row):
    def get(key):
        return (row.get(key) or "").strip()

    return {
        "local_decision_authority": AUTHORITY.get(get("local_decision_authority"), 0),
        "offering_fit": LEVEL.get(get("offering_fit"), 0),
        "trigger_signals": min(len(split_items(row.get("trigger_signals"))), 3),
        "deal_size_fit": LEVEL.get(get("deal_size_fit"), 0),
        "relationship_warmth": WARMTH.get(get("relationship_warmth"), 0),
        "persona_confidence": LEVEL.get(get("persona_confidence"), 0),
    }


def tier_for(score):
    if score >= 70:
        return "Invite"
    if score >= 40:
        return "Nurture"
    return "Deprioritize"


def badge_for(current_tier, tier):
    original = CURRENT_TIER.get((current_tier or "").strip())
    if original is None or TIER_RANK[original] == TIER_RANK[tier]:
        return "No change"
    return "Moved up" if TIER_RANK[tier] < TIER_RANK[original] else "Moved down"


def city_name(row):
    # "St. Petersburg FL" -> "St. Petersburg"
    city = (row.get("city") or "").strip()
    parts = city.rsplit(" ", 1)
    return parts[0] if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isupper() else city


def in_market(row):
    return (row.get("market") or "").strip() == "Tampa Bay"


def phrase_for(key, row):
    value = (row.get(key) or "").strip()
    if key == "local_decision_authority":
        if not in_market(row):
            return f"the executives sit outside Tampa Bay in {city_name(row)}"
        return {
            "Yes": f"the buying decision is made locally in {city_name(row)}",
            "Partial": "the buying decision is shared with an out-of-market HQ",
        }.get(value, "the buying decision is made outside Tampa Bay")
    if key == "trigger_signals":
        items = split_items(row.get("trigger_signals"))
        return f"they have live priorities ({', '.join(items[:3])})" if items else "there is no live trigger"
    return PHRASES[key].get(value, f"{key.replace('_', ' ')} is unknown")


def reason_for(pts, row):
    # Names the two signals that contributed the most points (requirement 5).
    # sorted() is stable, so ties follow WEIGHTS order.
    ranked = sorted(WEIGHTS, key=lambda k: WEIGHTS[k] * pts[k], reverse=True)[:2]
    text = f"{phrase_for(ranked[0], row)}, and {phrase_for(ranked[1], row)}."
    return text[0].upper() + text[1:]


def reason_codes_for(row):
    """Short executive-facing labels derived from the row. Order: locality, seniority,
    triggers, relationship, then fit gaps worth knowing about."""
    get = lambda key: (row.get(key) or "").strip()  # noqa: E731
    codes = []

    # 1. Where the decision is made.
    authority = get("local_decision_authority")
    if not in_market(row):
        codes.append(f"Outside Tampa Bay ({city_name(row)})")
    elif authority == "Yes":
        codes.append(f"Local decision maker ({city_name(row)})")
    elif authority == "Partial":
        codes.append("Shared decision with remote HQ")
    else:
        codes.append("Decided outside Tampa Bay")

    # 2. Who will be in the room.
    titles = split_items(row.get("target_persona"))
    if any(t.split()[0].upper() in C_SUITE for t in titles):
        codes.append("C-suite in the room")
    elif titles:
        codes.append("VP-level audience")

    # 3. Why now.
    triggers = split_items(row.get("trigger_signals"))
    for trigger in triggers:
        lower = trigger.lower()
        if lower.startswith("new "):
            code = f"New {trigger[4:]} in first 100 days"
        else:
            code = next((label for key, label in TRIGGER_CODES if key in lower), trigger[:1].upper() + trigger[1:])
        if code not in codes:
            codes.append(code)
    if len(triggers) >= 3:
        codes.append("Multiple live priorities")
    if not triggers:
        codes.append("No live trigger")

    # 4. Relationship.
    codes.append({"Warm": "Warm executive relationship", "Known": "Known to the team"}.get(
        get("relationship_warmth"), "Net-new relationship"))

    # 5. Fit strengths and gaps.
    if get("offering_fit") == "High":
        codes.append("Offering matches a stated priority")
    elif get("offering_fit") in ("Low", ""):
        codes.append("Weak offering fit")
    if get("deal_size_fit") == "High":
        codes.append("Deal size in sweet spot")
    elif get("deal_size_fit") in ("Low", ""):
        codes.append("Deal size below target")
    if get("persona_confidence") in ("Low", ""):
        codes.append("Executive not yet confirmed")
    return codes


def score_accounts(rows):
    scored = []
    for row in rows:
        pts = points(row)
        total = sum(WEIGHTS[k] * pts[k] for k in WEIGHTS)
        score = (2 * total + 3) // 6  # round(total / 3), half up
        tier = tier_for(score)
        scored.append(
            {
                "company": row["company"],
                "score": score,
                "tier": tier,
                "badge": badge_for(row.get("current_tier"), tier),
                "reason": reason_for(pts, row),
                "reason_codes": reason_codes_for(row),
                "highly_recommended": tier == "Invite" and score >= HIGHLY_RECOMMENDED_MIN,
            }
        )
    return sorted(scored, key=lambda a: -a["score"])  # stable: ties keep CSV order


def build_invite_list(scored, rows, room_size=40):
    personas = {r["company"]: split_items(r.get("target_persona")) for r in rows}
    accounts = []
    executive_count = 0
    for account in scored:
        if account["tier"] != "Invite":
            continue
        titles = personas.get(account["company"], [])
        if executive_count + len(titles) > room_size:
            break
        accounts.append(
            {
                "company": account["company"],
                "score": account["score"],
                "executives": len(titles),
                "personas": titles,
                "reason": account.get("reason", ""),
                "reason_codes": account.get("reason_codes", []),
                "highly_recommended": account.get("highly_recommended", False),
            }
        )
        executive_count += len(titles)
    return {"room_size": room_size, "accounts": accounts, "executive_count": executive_count}


def draft_spend_request(budget, invite_list, justification):
    count = invite_list["executive_count"]
    if count <= 0:
        raise ValueError("Invite list has no executives, cannot draft a spend request.")
    return {
        "budget": budget,
        "accounts": invite_list["accounts"],
        "executive_count": count,
        "cost_per_executive": (2 * budget + count) // (2 * count),  # half up
        "justification": justification,
        "status": "Pending Approval",
    }
