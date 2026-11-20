# Design: Royal Table · Account Growth Agent

Short by intent. This is a 2 hour build, so there are three files and no extra layers.

## Files

| File | Contents |
|---|---|
| `tools.py` | CSV loader and the three tools as pure functions. No Streamlit, boto3 or global state. |
| `test_tools.py` | pytest tests for `tools.py`, using the assertions from the success criteria. |
| `app.py` | Streamlit UI, tool schemas, the dispatcher, the Bedrock agent loop, session state, approval buttons and log. |
| `requirements.txt` | `streamlit`, `boto3`, `pytest`. |

## The three tools (`tools.py`)

```
load_accounts(path) -> list[dict]                     # csv.DictReader, one dict per row
score_accounts(rows) -> list[dict]                    # sorted by score, highest first
build_invite_list(scored, rows, room_size=40) -> dict
draft_spend_request(budget, invite_list, justification) -> dict
```

**`score_accounts`** returns one dict per account: `company`, `score`, `tier`, `badge`, `reason`.
- Points per signal follow requirement 2. Score is `sum(weight * points / 3)` rounded half up, computed as `(2 * S + 3) // 6` where `S = sum(weight * points)`. This avoids Python's banker's rounding.
- Tier: 70 and above is Invite, 40 to 69 Nurture, below 40 Deprioritize.
- Badge: `current_tier` Tier 1, 2, 3 map to Invite, Nurture, Deprioritize and are compared with the new tier. A better tier is Moved up, a worse one is Moved down, the same is No change.
- Reason: the two signals with the highest `weight * points / 3`. Ties are broken by the fixed signal order (authority, offering fit, triggers, deal size, warmth, persona confidence). Template: `"Strong offering fit and active trigger signals"`, using one fixed phrase per signal. No LLM is involved.
- Sorting is stable, so tied scores keep CSV order.

**`build_invite_list`** takes the scored list and the raw rows. It looks up each company's `target_persona` and counts the semicolon separated titles (trimmed, blanks ignored) as executives. It walks Invite accounts in score order, and stops at the first account that would exceed `room_size`. It returns `{"room_size", "accounts": [{company, score, executives, personas}], "executive_count"}`.

**`draft_spend_request`** returns `{"budget", "accounts", "executive_count", "cost_per_executive", "justification", "status": "Pending Approval"}`.
- `cost_per_executive` is `budget / executive_count`, rounded half up to a whole dollar. 25000 / 14 gives 1786.
- The status is a constant. The function has no status parameter and no other code path sets one.
- If `executive_count` is 0, it raises `ValueError` and the dispatcher returns it as a tool error. The request is not created.

**Highly recommended** (requirement 13): `score_accounts` adds `highly_recommended = tier == "Invite" and score >= 90` (constant `HIGHLY_RECOMMENDED_MIN`). `build_invite_list` copies it. It is a label only.

## Decision board (`app.py`)

Shown after a run, above the spend request, built only from tool outputs in session state:
- Four metric cards: scored, Invite, highly recommended, and a room fill progress bar.
- One HTML card per highly recommended account (city and titles looked up from the loaded rows).
- An Altair horizontal bar chart of scores coloured by tier (navy Invite, orange Nurture, grey Deprioritize) with rules at 70 and 90. Altair ships with Streamlit, so `requirements.txt` does not change.

## Agent loop (`app.py`)

The agent never sees the whole dataset and never passes data between tools. The model supplies only small arguments. The dispatcher supplies the data from session state, so the model cannot invent numbers.

| Tool name | Model supplies | Dispatcher supplies |
|---|---|---|
| `score_accounts` | nothing | the loaded rows |
| `build_invite_list` | `room_size` | the scored list and rows |
| `draft_spend_request` | `budget`, `justification` | the invite list from the previous call |

The dispatcher overrides `room_size` and `budget` with the values from the UI inputs, so the model can't change them. The tool schemas still declare both arguments, as the requirements describe.

Loop, using `bedrock-runtime` `converse`:
1. Create the client with `boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])`. If `BEDROCK_MODEL_ID` or `AWS_REGION` is unset, show an error naming it and stop before any call.
2. Send the system prompt, one user message that states the budget and room size, and `toolConfig` with the three tool specs.
3. While `stopReason == "tool_use"`: for each `toolUse` block, run the dispatcher and record `{name, input, output}`. Append the assistant message, then a user message containing one `toolResult` per `toolUse`. On a tool exception, return `status: "error"` in the `toolResult` and record the error.
4. Stop when `stopReason` is `end_turn`, or after 6 turns to avoid a runaway loop.
5. The run is valid only if `draft_spend_request` was called. If not, show "Agent did not draft a spend request" and create no request.

**System prompt** (requirement 9): use tools for every number, explain which accounts moved and why in no more than three sentences, and finish by calling `draft_spend_request`.

**Credentials:** only boto3's default chain. No keys in code or in the UI.

## Session state

| Key | Value |
|---|---|
| `rows` | accounts loaded once from `data/tampa_target_accounts.csv` |
| `scored` | latest `score_accounts` output |
| `invite_list` | latest `build_invite_list` output |
| `tool_calls` | list of `{name, input, output}` for display |
| `agent_summary` | the agent's final text |
| `request` | the spend request dict, or `None` |
| `log` | list of `{timestamp, actor, action, reason}` |

Pressing Run agent clears everything except `rows`, then starts a new run.

## Approval flow

- Approve and Reject are rendered only when `request["status"] == "Pending Approval"`. They are plain Streamlit buttons next to one reason text input.
- A click handler in `app.py` does the following. If the reason is blank, show an error and return, leaving the status unchanged. Otherwise set `status` to Approved or Rejected and add one Human log entry with the reason.
- That handler is the only place a status changes. It is not in the tool list, so the agent cannot call it.
- After approval or rejection, the buttons disappear on the next rerun.

## Log

- One Agent entry is added when a run finishes with a request: actor Agent, action "Drafted spend request", reason is the agent's justification. Failed runs add no entry and show an error.
- One Human entry is added per approve or reject click.

## Tests (`test_tools.py`)

These are in `tasks.md`, not here. They cover the success criteria: the four named scores, the invite lists for room sizes 40 and 10, and the $1,786 cost per executive. Agent and UI code are not unit tested, so there are no Bedrock mocks.

## Browser tests (`test_e2e.py`)

- Playwright (`pytest-playwright`, Chromium headless) drives a Streamlit instance the tests start on port 8599, with real Bedrock.
- Assertions check tool numbers and UI state only, never the agent's wording: header logo below the Streamlit toolbar; decision board 20 / 7 / 4 / 14 of 40 with four cards and the chart; 14 executives and $1,786; empty-reason error; Approve and Reject flows with the log.
- Status is read from the status pill, because the agent's text can also mention the status.
- Screenshots go to `test-results/` (git-ignored). A tall viewport is used because Streamlit scrolls inside its own container.

## Assumptions to confirm

1. **Dispatcher overrides model arguments.** The UI values for budget and room size always win over what the model passes.
2. **Zero executives** raises an error and no request is created. The requirements don't cover this case.
3. **Tool-call limit of 6 turns.** My choice, not in the requirements.
4. **Reason text** uses fixed phrases per signal. The requirements only say the reason names the two top signals.
