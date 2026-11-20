# Requirements: Royal Table · Account Growth Agent

## Introduction

Event spend decisions start with a target list nobody trusts. This feature scores Tampa Bay target accounts from one sample CSV with a fixed formula. An Amazon Bedrock agent uses three tools to build the invite list and draft an event spend request. A human must approve or reject the request. The agent cannot change a request's status.

**Name.** Royal Table is built to grow existing Royal Cyber accounts by deciding who earns a seat at an executive event. The metaphor maps onto every part of the app, and the UI uses it in short hints only:

| App part | Royal Table language |
|---|---|
| Room size, invite list | Seats at the table |
| Readiness score, reason codes | Earning a seat |
| Highly recommended (score 90+) | Head of the table |
| Spend request, cost per executive | The cost of the table, cost per seat |
| Account Manager approval | Confirm the table, then hand it to Marketing |
| Decision log | Who set the table, and why |

The folder name `target-curator-agent` and the URL path `/curator/` are kept from the earlier name, so existing links still work.

## Out of scope (hard limits)

- No adjustable weights or sliders. Charts are allowed only on the decision board (requirement 13). *(Changed at user request: previously "no charts".)*
- No event comparison. One event, one budget.
- No exports, printing or saving between sessions.
- No login, roles or approval levels.
- No CRM, email, procurement or payment systems.
- The agent never approves or changes a request status. Only the human does.
- The agent never calculates numbers. All numbers come from tools.
- No data other than the sample CSV.
- No knowledge bases, multi agent setups or fine tuning.

## Requirements

### 1. Load data
**User story:** As an events lead, I want the app to read the sample accounts, so that scoring starts from one known file.

1. WHEN the app starts, THE app SHALL load `data/tampa_target_accounts.csv`.
2. IF the file is missing or unreadable, THEN THE app SHALL show an error naming the file and SHALL NOT run the agent.

### 2. Signal points
1. THE `score_accounts` tool SHALL convert `local_decision_authority` to points: Yes 3, Partial 2, No 0.
2. THE `score_accounts` tool SHALL convert `offering_fit`, `deal_size_fit` and `persona_confidence` to points: High 3, Medium 2, Low 1, blank 0.
3. THE `score_accounts` tool SHALL convert `relationship_warmth` to points: Warm 3, Known 2, Cold 0.
4. THE `score_accounts` tool SHALL set `trigger_signals` points to the count of semicolon separated items, capped at 3.

### 3. Score
1. THE `score_accounts` tool SHALL use these fixed weights: `local_decision_authority` 20, `offering_fit` 25, `trigger_signals` 20, `deal_size_fit` 15, `relationship_warmth` 10, `persona_confidence` 10.
2. THE `score_accounts` tool SHALL calculate score as the sum of (weight × points ÷ 3) across the six signals, rounded to a whole number.

### 4. Tier
1. WHEN a score is 70 or above, THE `score_accounts` tool SHALL assign tier Invite.
2. WHEN a score is 40 to 69, THE `score_accounts` tool SHALL assign tier Nurture.
3. WHEN a score is below 40, THE `score_accounts` tool SHALL assign tier Deprioritize.

### 5. Score output
1. THE `score_accounts` tool SHALL return, for each account, company, score, tier, movement badge and reason.
2. THE `score_accounts` tool SHALL map `current_tier` Tier 1 to Invite, Tier 2 to Nurture and Tier 3 to Deprioritize, and set the badge to Moved up, Moved down or No change by comparing that value with the new tier.
3. THE `score_accounts` tool SHALL build each reason from the two signals that contributed the most points, in executive language (for example "the buying decision is made locally in Tampa").
4. THE `score_accounts` and `build_invite_list` tools SHALL return `reason_codes` for each account: short executive-facing labels derived only from the CSV, covering where the decision is made (Local decision maker, Shared decision with remote HQ, Decided outside Tampa Bay, Outside Tampa Bay), who is in the room (C-suite or VP-level), why now (one code per trigger, e.g. New CDO in first 100 days, Regulator deadline), relationship, and fit gaps. Reason codes SHALL NOT change scores or tiers.

### 6. Invite list
1. THE `build_invite_list` tool SHALL take a room size, defaulting to 40.
2. THE `build_invite_list` tool SHALL count each semicolon separated title in `target_persona` as one executive.
3. THE `build_invite_list` tool SHALL return Invite tier accounts in score order until adding the next account would exceed the room size.

### 7. Spend request
1. THE `draft_spend_request` tool SHALL take a budget, the invite list and a justification.
2. THE `draft_spend_request` tool SHALL return the invited accounts, the executive count, cost per executive and status Pending Approval.
3. THE `draft_spend_request` tool SHALL calculate cost per executive as budget ÷ executive count, rounded to the nearest dollar.
4. THE `draft_spend_request` tool SHALL NOT return any status other than Pending Approval.

### 8. Bedrock agent
1. THE agent SHALL use the Amazon Bedrock Converse API with tool use through boto3.
2. THE app SHALL read the model ID from `BEDROCK_MODEL_ID` and the region from `AWS_REGION`.
3. IF either variable is not set, THEN THE app SHALL show an error naming the missing variable and SHALL NOT call Bedrock.
4. THE app SHALL obtain AWS credentials from the standard AWS credential chain and SHALL NOT contain hard coded keys.

### 9. System prompt
1. THE agent system prompt SHALL instruct the agent to use tools for every number.
2. THE agent system prompt SHALL instruct the agent to explain which accounts moved and why in no more than three sentences.
3. THE agent system prompt SHALL instruct the agent to finish by calling `draft_spend_request`.

### 10. UI inputs and results
1. THE UI SHALL provide a budget input defaulting to 25000, a room size input defaulting to 40, and a Run agent button.
2. WHEN the user clicks Run agent, THE UI SHALL show the scored accounts table, each tool call with its inputs and outputs, and the spend request.

### 11. Approval
1. WHILE the spend request status is Pending Approval, THE UI SHALL show Approve and Reject buttons.
2. WHILE the status is not Pending Approval, THE UI SHALL NOT show Approve or Reject buttons.
3. WHEN the user clicks Approve with a non-empty reason, THE app SHALL set the status to Approved.
4. WHEN the user clicks Reject with a non-empty reason, THE app SHALL set the status to Rejected.
5. IF the reason is empty, THEN THE app SHALL show an error and SHALL NOT change the status.
6. THE app SHALL change the status only from a human click, never from an agent tool call.

### 12. Log
1. THE UI SHALL show a log with timestamp, actor (Agent or Human), action and reason.
2. WHEN the agent run finishes, THE app SHALL add one Agent entry.
3. WHEN the user approves or rejects, THE app SHALL add one Human entry containing the reason.

### 13. Highly recommended and decision board
**User story:** As an Account Manager, I want the strongest accounts called out and the whole picture on one screen, so that I can decide in seconds and share the screen as an information radiator.

1. THE `score_accounts` tool SHALL set `highly_recommended` to true for an account WHEN its tier is Invite AND its score is 90 or above, and false otherwise.
2. THE `build_invite_list` tool SHALL carry `highly_recommended` through for each invited account.
3. Highly recommended SHALL NOT change scores, tiers, the invite list or the cost per executive.
4. WHEN a run has scored accounts, THE UI SHALL show a decision board above the spend request containing:
   - counts of accounts scored, Invite tier accounts and highly recommended accounts,
   - room fill as invited executives out of room size,
   - one card per highly recommended account with company, score, city, executive titles and its top three reason codes,
   - a horizontal bar chart of every account's score, coloured by tier, with marker lines at 70 (Invite) and 90 (Highly recommended).
5. THE UI SHALL mark highly recommended accounts with ⭐ in the account tables.
6. THE agent system prompt SHALL instruct the agent to lead its explanation with the highly recommended accounts.

## Success criteria (from the feature description)

- Unit tests assert: Suncoast Credit Union 100 Invite Moved up; Raymond James 92 Invite No change; Citi 48 Nurture Moved down; Bank of America 17 Deprioritize Moved down.
- Room size 40 gives 7 accounts and 14 executives. Room size 10 gives 5 accounts and 10 executives.
- Budget 25000 with room size 40 gives cost per executive $1,786.
- A run shows tool calls for `score_accounts`, `build_invite_list` and `draft_spend_request`.
- The request stays Pending Approval until a human clicks Approve or Reject.
- Approve with an empty reason shows an error and leaves the status unchanged.
- After approval, the log shows one Agent entry and one Human entry.
- With default inputs, exactly four accounts are highly recommended: Suncoast Credit Union (100), BayFirst Financial (97), Raymond James (92) and GTE Financial (90).
- The decision board shows 20 scored, 7 Invite, 4 highly recommended and room fill 14 of 40, with four cards and a score chart.

## Constraints

- Python 3.11 or later, Streamlit, boto3, pytest.
- Files: `app.py`, `tools.py` (three pure functions), `test_tools.py`, plus `requirements.txt`.
- Browser tests *(added at user request)*: `test_e2e.py` with Playwright, against real Bedrock. Test-only dependencies in `requirements-dev.txt`. The browser tests skip when `BEDROCK_MODEL_ID` is not set.
- All state in Streamlit session state. No database.
- Runs with `pip install -r requirements.txt` and `streamlit run app.py`.

## Decisions and open items

1. **Data file: resolved.** `data/tampa_target_accounts.csv` now exists and is identical to `public/sample/tampa_target_accounts.csv`.
2. **Stack: resolved.** Python and Streamlit (option C). The Python files live at the repo root, next to the React app. `product.md`, `tech.md` and `structure.md` now describe both apps.
3. **Open: log entry count.** Requirement 12 asks for "one Agent entry", while requirement 10 shows each tool call separately. I wrote it as one Agent entry per completed run. Say so if you want one per tool call.
4. **Accepted: scoring is duplicated** in `src/scoring.ts` and `tools.py`. The two must match.
5. **Open: Python packages** (`boto3`, `streamlit`, `pytest`) are not installed. They will be installed in a virtual environment during project setup.
