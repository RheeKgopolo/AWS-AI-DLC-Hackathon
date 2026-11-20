from tools import (
    build_invite_list,
    draft_spend_request,
    load_accounts,
    score_accounts,
)

rows = load_accounts("data/tampa_target_accounts.csv")
scored = score_accounts(rows)
by_company = {a["company"]: a for a in scored}


def check(company, score, tier, badge):
    account = by_company[company]
    assert account["score"] == score
    assert account["tier"] == tier
    assert account["badge"] == badge


def test_suncoast():
    check("Suncoast Credit Union", 100, "Invite", "Moved up")


def test_raymond_james():
    check("Raymond James", 92, "Invite", "No change")


def test_citi():
    check("Citi", 48, "Nurture", "Moved down")


def test_bank_of_america():
    check("Bank of America", 17, "Deprioritize", "Moved down")


def test_invite_list_room_40():
    invite = build_invite_list(scored, rows, 40)
    assert len(invite["accounts"]) == 7
    assert invite["executive_count"] == 14


def test_invite_list_room_10():
    invite = build_invite_list(scored, rows, 10)
    assert len(invite["accounts"]) == 5
    assert invite["executive_count"] == 10


def test_cost_per_executive():
    invite = build_invite_list(scored, rows, 40)
    request = draft_spend_request(25000, invite, "test")
    assert request["cost_per_executive"] == 1786
    assert request["status"] == "Pending Approval"
