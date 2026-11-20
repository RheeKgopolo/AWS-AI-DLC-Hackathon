"""Royal Table · Account Growth Agent (Streamlit UI and Bedrock agent loop).

Flow: the Account Manager sets budget and room size and clicks Run agent. run_agent() calls
the Bedrock Converse API with three tool specs. dispatch() runs each requested tool from
tools.py, using data from session state and the UI's budget and room size. The spend
request is always created as Pending Approval. Only decide(), triggered by the Approve
or Reject buttons, changes its status, and it requires a reason.

Config: BEDROCK_MODEL_ID and AWS_REGION environment variables, AWS credentials from the
standard chain. See README.md for running behind the IDE proxy and for tests.
"""

import base64
import html
import json
import logging
import os
import time
import uuid
from datetime import datetime

import altair as alt
import boto3
import streamlit as st

from tools import build_invite_list, draft_spend_request, load_accounts, score_accounts

DATA_PATH = "data/tampa_target_accounts.csv"

# Structured logging: one JSON line per event on stderr (the Streamlit terminal).
# Logs run metadata, tool timings, Bedrock latency and token counts, errors and decisions.
# Never logs credentials, prompts or full tool outputs. Set LOG_LEVEL=DEBUG for more.
log = logging.getLogger("royal_table")
if not log.handlers:  # Streamlit re-runs this script on every interaction
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(_handler)
    log.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    log.propagate = False


def log_event(event, level=logging.INFO, **fields):
    log.log(level, json.dumps({"event": event, **fields}, default=str))

MAX_TURNS = 6

SYSTEM_PROMPT = (
    "You are Royal Table, the account growth agent for Royal Cyber. You decide which "
    "executives earn a seat at an executive event to grow existing accounts. "
    "Use tools for every number. Never calculate or estimate numbers yourself. "
    "Call score_accounts, then build_invite_list, then explain which accounts moved "
    "and why in no more than three sentences of plain prose, no lists or headings. "
    "Explain moves using the reason_codes the tools return, in the executives' language. "
    "Lead with the accounts where highly_recommended is true. "
    "Finish by calling draft_spend_request with a short justification."
)

TOOL_SPECS = [
    {
        "toolSpec": {
            "name": "score_accounts",
            "description": "Score every target account and return company, score, tier, badge and reason.",
            "inputSchema": {"json": {"type": "object", "properties": {}}},
        }
    },
    {
        "toolSpec": {
            "name": "build_invite_list",
            "description": "Build the invite list from Invite tier accounts for a room size.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {"room_size": {"type": "integer"}},
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "draft_spend_request",
            "description": "Draft the spend request for the invite list. Status is always Pending Approval.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "budget": {"type": "number"},
                        "justification": {"type": "string"},
                    },
                    "required": ["justification"],
                }
            },
        }
    },
]


TIER_ICON = {"Invite": "🟢 Invite", "Nurture": "🟡 Nurture", "Deprioritize": "⚪ Deprioritize"}
BADGE_ICON = {"Moved up": "▲ Moved up", "Moved down": "▼ Moved down", "No change": "– No change"}
DISPLAY_NAMES = {
    "company": "Company", "score": "Score", "tier": "Tier", "badge": "Movement",
    "executives": "Execs", "personas": "Titles", "reason": "Why now", "reason_codes": "Reason codes",
}


def for_display(items):
    """Readable table rows. Tool outputs are unchanged."""
    rows = []
    for item in items:
        row = {}
        for key, value in item.items():
            if key == "highly_recommended":
                continue
            if key == "company" and item.get("highly_recommended"):
                value = f"⭐ {value}"
            if key == "reason_codes" or key == "personas":
                value = " · ".join(value)
            elif key == "tier":
                value = TIER_ICON.get(value, value)
            elif key == "badge":
                value = BADGE_ICON.get(value, value)
            row[DISPLAY_NAMES.get(key, key)] = value
        rows.append(row)
    return rows


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_log(actor, action, reason):
    st.session_state.log.append(
        {"timestamp": now(), "actor": actor, "action": action, "reason": reason}
    )


def init_state():
    defaults = {
        "rows": None,
        "scored": None,
        "invite_list": None,
        "tool_calls": [],
        "agent_summary": "",
        "request": None,
        "log": [],
        "error": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def dispatch(name, args, budget, room_size):
    """Run a tool. Budget and room size always come from the UI, not the model."""
    state = st.session_state
    if name == "score_accounts":
        state.scored = score_accounts(state.rows)
        return state.scored
    if name == "build_invite_list":
        if state.scored is None:
            raise ValueError("Call score_accounts first.")
        state.invite_list = build_invite_list(state.scored, state.rows, room_size)
        return state.invite_list
    if name == "draft_spend_request":
        if state.invite_list is None:
            raise ValueError("Call build_invite_list first.")
        state.request = draft_spend_request(
            budget, state.invite_list, args.get("justification", "")
        )
        return state.request
    raise ValueError(f"Unknown tool: {name}")


def run_agent(budget, room_size):
    state = st.session_state
    for key in ("BEDROCK_MODEL_ID", "AWS_REGION"):
        if not os.environ.get(key):
            state.error = f"Environment variable {key} is not set."
            log_event("config_error", logging.ERROR, missing=key)
            return
    run_id = uuid.uuid4().hex[:8]
    model_id = os.environ["BEDROCK_MODEL_ID"]
    started = time.perf_counter()
    tokens = {"input": 0, "output": 0}
    log_event("run_start", run_id=run_id, model=model_id, budget=budget, room_size=room_size)
    client = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": f"Curate the invite list for our Tampa Bay event. "
                    f"Budget: ${budget:,}. Room size: {room_size}."
                }
            ],
        }
    ]
    for turn in range(1, MAX_TURNS + 1):
        t0 = time.perf_counter()
        try:
            response = client.converse(
                modelId=model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=messages,
                toolConfig={"tools": TOOL_SPECS},
            )
        except Exception as exc:
            log_event("bedrock_error", logging.ERROR, run_id=run_id, turn=turn,
                      error=type(exc).__name__, detail=str(exc)[:300])
            raise
        usage = response.get("usage", {})
        tokens["input"] += usage.get("inputTokens", 0)
        tokens["output"] += usage.get("outputTokens", 0)
        log_event("bedrock_call", run_id=run_id, turn=turn, stop_reason=response.get("stopReason"),
                  latency_ms=response.get("metrics", {}).get("latencyMs"),
                  wall_ms=round((time.perf_counter() - t0) * 1000),
                  input_tokens=usage.get("inputTokens"), output_tokens=usage.get("outputTokens"))
        message = response["output"]["message"]
        messages.append(message)
        texts = [b["text"] for b in message["content"] if "text" in b]
        if texts:
            state.agent_summary = "\n\n".join(texts)
        if response["stopReason"] != "tool_use":
            break
        results = []
        for block in message["content"]:
            if "toolUse" not in block:
                continue
            use = block["toolUse"]
            t0 = time.perf_counter()
            try:
                output = dispatch(use["name"], use["input"], budget, room_size)
                status = "success"
            except Exception as exc:  # report the error to the model and the UI
                output = {"error": str(exc)}
                status = "error"
            log_event("tool_call", logging.INFO if status == "success" else logging.WARNING,
                      run_id=run_id, tool=use["name"], status=status,
                      ms=round((time.perf_counter() - t0) * 1000),
                      model_args=use["input"] if use["name"] != "draft_spend_request" else
                      {k: v for k, v in use["input"].items() if k != "justification"},
                      error=output.get("error") if status == "error" else None)
            state.tool_calls.append(
                {"name": use["name"], "input": use["input"], "output": output}
            )
            payload = output if isinstance(output, dict) else {"result": output}
            results.append(
                {
                    "toolResult": {
                        "toolUseId": use["toolUseId"],
                        "content": [{"json": payload}],
                        "status": status,
                    }
                }
            )
        messages.append({"role": "user", "content": results})
    elapsed = round((time.perf_counter() - started) * 1000)
    if state.request is None:
        state.error = "Agent did not draft a spend request."
        log_event("run_end", logging.WARNING, run_id=run_id, outcome="no_request", turns=turn,
                  ms=elapsed, input_tokens=tokens["input"], output_tokens=tokens["output"])
    else:
        add_log("Agent", "Drafted spend request", state.request["justification"])
        log_event("run_end", run_id=run_id, outcome="pending_approval", turns=turn, ms=elapsed,
                  accounts=len(state.request["accounts"]),
                  executives=state.request["executive_count"],
                  cost_per_executive=state.request["cost_per_executive"],
                  input_tokens=tokens["input"], output_tokens=tokens["output"])


def decide(status, reason):
    if not reason.strip():
        st.error("A reason is required.")
        log_event("decision_rejected_empty_reason", logging.WARNING, attempted=status)
        return
    st.session_state.request["status"] = status
    add_log("Human", status, reason.strip())
    log_event("decision", status=status, reason_chars=len(reason.strip()))
    st.rerun()


# Royal Cyber brand palette, taken from the Elementor global colours on royalcyber.com
# (--e-global-color-primary, -secondary, -text and the light blue surface).
BRAND = {
    "primary": "#003963",  # navy: logo, headings, primary buttons
    "accent": "#E66208",   # orange: heading rules, button hover
    "text": "#2C2D2E",
    "surface": "#E9F1FF",  # light blue: cards
    "border": "#CECECE",
}
# Official logo from royalcyber.com (wp-content/uploads/2018/04/Royal-Cyber-Logo.svg).
LOGO_PATH = "assets/royal_cyber_logo.svg"
LOGO_SVG = None
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_SVG = base64.b64encode(f.read()).decode()

st.set_page_config(page_title="Royal Table · Royal Cyber", layout="wide")

st.markdown(
    f"""
    <style>
    /* Clear Streamlit's fixed top toolbar (about 3.75rem) so the header is never covered. */
    .block-container {{max-width: 1200px; padding-top: 4.5rem;}}
    h1 {{color: {BRAND["primary"]}; margin: 0;}}
    h3 {{color: {BRAND["primary"]}; border-bottom: 2px solid {BRAND["accent"]};
        padding-bottom: .3rem; margin-top: 1.5rem;}}
    [data-testid="stMetric"] {{background: {BRAND["surface"]}; border: 1px solid {BRAND["border"]};
        border-left: 4px solid {BRAND["primary"]}; border-radius: 8px; padding: .6rem .9rem;}}
    .stButton button[kind="primary"] {{background: {BRAND["primary"]}; border-color: {BRAND["primary"]};}}
    .stButton button[kind="primary"]:hover {{background: {BRAND["accent"]}; border-color: {BRAND["accent"]};}}
    .brandbar {{display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap;
        padding-bottom: .8rem; border-bottom: 3px solid {BRAND["primary"]}; margin-bottom: 1rem;}}
    .brandbar img {{height: 48px; width: auto; display: block; flex-shrink: 0;}}
    .brandbar .divider {{width: 2px; align-self: stretch; background: {BRAND["accent"]};}}
    .brandbar .apptitle {{font-size: 1.6rem; font-weight: 700; color: {BRAND["primary"]}; line-height: 1.2;}}
    .brandbar .roles {{margin: .15rem 0 0 0;}}
    .wordmark {{font-weight: 800; font-size: 1.4rem; letter-spacing: .04em; color: {BRAND["primary"]};}}
    .wordmark span {{color: {BRAND["accent"]};}}
    .pill {{display: inline-block; padding: .2rem .7rem; border-radius: 999px;
        font-weight: 600; font-size: .9rem;}}
    .pill-pending {{background: #fff4d6; color: #8a5a00;}}
    .pill-approved {{background: #dcf5e3; color: #146c2e;}}
    .pill-rejected {{background: #fde2e1; color: #a1251b;}}
    .roles {{color: {BRAND["text"]}; font-size: .95rem;}}
    .brandbar .descriptor {{font-size: 1rem; font-weight: 600; color: {BRAND["accent"]}; margin-left: .4rem;}}
    .brandbar .tagline {{margin: .1rem 0 0 0; font-style: italic; color: {BRAND["primary"]};}}
    .card {{background: #fff; border: 1px solid {BRAND["border"]}; border-top: 5px solid {BRAND["accent"]};
        border-radius: 10px; padding: .8rem 1rem; height: 100%;}}
    .card .label {{color: {BRAND["accent"]}; font-weight: 700; font-size: .72rem; letter-spacing: .08em;}}
    .card .name {{color: {BRAND["primary"]}; font-weight: 700; font-size: 1.05rem; margin: .15rem 0;}}
    .card .score {{color: {BRAND["primary"]}; font-weight: 800; font-size: 2rem; line-height: 1;}}
    .card .score small {{font-size: .8rem; font-weight: 600; color: {BRAND["text"]};}}
    .card .meta {{color: {BRAND["text"]}; font-size: .82rem; margin: .35rem 0;}}
    .chip {{display: inline-block; background: {BRAND["surface"]}; color: {BRAND["primary"]};
        border-radius: 999px; padding: .1rem .55rem; font-size: .74rem; margin: .12rem .15rem 0 0;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# One header row: logo on the left, title and audience line on the right.
logo_html = (
    f'<img src="data:image/svg+xml;base64,{LOGO_SVG}" alt="Royal Cyber">'
    if LOGO_SVG
    else '<div class="wordmark">ROYAL <span>CYBER</span></div>'
)
st.markdown(
    f"""<div class="brandbar">{logo_html}<div class="divider"></div><div>
    <div class="apptitle">Royal Table <span class="descriptor">Account Growth Agent</span></div>
    <p class="tagline">Who earns a seat at the Royal table</p>
    <p class="roles">Tampa Bay executive event · For <b>Account Managers</b> growing Royal Cyber
    accounts. Marketing runs the campaign from the confirmed table.</p></div></div>""",
    unsafe_allow_html=True,
)
init_state()

try:
    if st.session_state.rows is None:
        st.session_state.rows = load_accounts(DATA_PATH)
except OSError:
    st.error(f"Cannot read {DATA_PATH}.")
    st.stop()

with st.container(border=True):
    st.markdown("**Set the table**")
    col1, col2, col3 = st.columns([2, 2, 1])
    budget = col1.number_input("Budget (USD)", min_value=1, value=25000, step=1000,
                                help="The cost of the table for the whole event.")
    room_size = col2.number_input("Room size (executives)", min_value=1, value=40, step=1,
                                   help="Seats at the table. Each executive title takes one seat.")
    col3.write("")
    run = col3.button("Run agent", type="primary", width="stretch",
                      help="Scores every account, fills the seats and drafts the spend request for your approval.")

if run:
    for key in ("scored", "invite_list", "request", "agent_summary", "error"):
        st.session_state[key] = None if key in ("scored", "invite_list", "request") else ""
    st.session_state.tool_calls = []
    st.session_state.log = []
    try:
        with st.spinner("Agent is scoring accounts and drafting the spend request..."):
            run_agent(int(budget), int(room_size))
    except Exception as exc:
        st.session_state.error = f"Bedrock call failed: {exc}"
        log.exception("run_failed")

if st.session_state.error:
    st.error(st.session_state.error)

def render_decision_board():
    """Information radiator built only from tool outputs (requirement 13)."""
    state = st.session_state
    scored = state.scored
    invite = state.invite_list
    top = [a for a in scored if a.get("highly_recommended")]
    rows = {r["company"]: r for r in state.rows}

    st.subheader("Decision board")
    st.caption("Who earns a seat, at a glance.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accounts scored", len(scored), help="Every account considered for a seat.")
    c2.metric("Invite tier", sum(a["tier"] == "Invite" for a in scored), help="Earned a seat: score 70 or above.")
    c3.metric("⭐ Highly recommended", len(top), help="Head of the table: Invite tier and score 90 or above.")
    if invite:
        seats, room = invite["executive_count"], invite["room_size"]
        c4.metric("Room fill", f"{seats} / {room}", help="Seats filled out of seats at the table.")
        c4.progress(min(seats / room, 1.0))

    if top:
        st.markdown("**⭐ Head of the table** · highly recommended, invite first")
        for col, account in zip(st.columns(len(top)), top):
            row = rows.get(account["company"], {})
            # CSV values are untrusted: escape everything rendered with unsafe_allow_html.
            esc = html.escape
            titles = esc(" · ".join(t.strip() for t in row.get("target_persona", "").split(";") if t.strip()))
            chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in account["reason_codes"][:3])
            col.markdown(
                f"""<div class="card"><div class="label">HIGHLY RECOMMENDED</div>
                <div class="name">{esc(account["company"])}</div>
                <div class="score">{account["score"]}<small> / 100</small></div>
                <div class="meta">{esc(row.get("city", ""))} · {titles}</div>{chips}</div>""",
                unsafe_allow_html=True,
            )

    chart_rows = [
        {"Company": ("⭐ " if a.get("highly_recommended") else "") + a["company"],
         "Score": a["score"], "Tier": a["tier"]}
        for a in scored
    ]
    bars = alt.Chart(alt.Data(values=chart_rows)).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Readiness score"),
        y=alt.Y("Company:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=260, labelOverlap=False, labelFontSize=12)),
        color=alt.Color(
            "Tier:N",
            scale=alt.Scale(
                domain=["Invite", "Nurture", "Deprioritize"],
                range=[BRAND["primary"], BRAND["accent"], BRAND["border"]],
            ),
            legend=alt.Legend(orient="top", title=None),
        ),
        tooltip=["Company:N", "Score:Q", "Tier:N"],
    )
    rules = alt.Chart(alt.Data(values=[
        {"x": 70, "label": "Invite 70"}, {"x": 90, "label": "Highly recommended 90"},
    ])).mark_rule(strokeDash=[4, 3], color=BRAND["text"]).encode(x="x:Q")
    labels = rules.mark_text(align="right", dx=-4, dy=-6, fontSize=11, color=BRAND["text"]).encode(
        text="label:N", y=alt.value(0))
    st.altair_chart((bars + rules + labels).properties(height=28 * len(chart_rows) + 40),
                    width="stretch")


if st.session_state.scored:
    render_decision_board()

request = st.session_state.request

if request:
    st.subheader("Spend request")
    st.caption("The cost of the table.")
    css = {"Pending Approval": "pending", "Approved": "approved", "Rejected": "rejected"}
    st.markdown(
        f'<span class="pill pill-{css.get(request["status"], "pending")}">'
        f'{html.escape(request["status"])}</span>',
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accounts invited", len(request["accounts"]))
    m2.metric("Executives", request["executive_count"])
    m3.metric("Budget", f"${request['budget']:,}")
    m4.metric("Cost per executive", f"${request['cost_per_executive']:,}", help="Cost per seat: budget divided by executives.")
    st.markdown(f"**Justification:** {request['justification']}")
    st.dataframe(for_display(request["accounts"]), width="stretch", hide_index=True)

    if request["status"] == "Pending Approval":
        with st.container(border=True):
            st.markdown("**Confirm the table** · once approved, Marketing runs the campaign")
            reason = st.text_input("Reason (required)", key="reason")
            approve_col, reject_col, _ = st.columns([1, 1, 4])
            if approve_col.button("Approve", type="primary", width="stretch"):
                decide("Approved", reason)
            if reject_col.button("Reject", width="stretch"):
                decide("Rejected", reason)

if st.session_state.agent_summary:
    st.subheader("Agent recommendation")
    st.caption("Why these seats.")
    st.info(st.session_state.agent_summary)

if st.session_state.scored:
    st.subheader("All scored accounts")
    st.caption("🟢 Invite · 🟡 Nurture · ⚪ Deprioritize   |   ▲ moved up · ▼ moved down from the original tier")
    st.dataframe(for_display(st.session_state.scored), width="stretch", hide_index=True)

if st.session_state.log:
    st.subheader("Decision log")
    st.caption("Who set the table, and why.")
    st.dataframe(st.session_state.log, width="stretch", hide_index=True)

if st.session_state.tool_calls:
    with st.expander(f"Agent tool calls ({len(st.session_state.tool_calls)}) · for audit"):
        for call in st.session_state.tool_calls:
            st.markdown(f"**{call['name']}**")
            st.write("Input")
            st.json(call["input"])
            st.write("Output")
            st.json(call["output"], expanded=False)
