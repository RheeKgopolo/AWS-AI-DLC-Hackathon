"""Builds docs/royal-table-hackathon.pptx. Run:
    uv run --python 3.11 --with python-pptx python docs/deck/build_deck.py
"""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from PIL import Image
from lxml import etree

D = "docs/deck/"
NAVY, ORANGE, TEXT = RGBColor(0x00, 0x39, 0x63), RGBColor(0xE6, 0x62, 0x08), RGBColor(0x2C, 0x2D, 0x2E)
LIGHT, GREY, WHITE = RGBColor(0xE9, 0xF1, 0xFF), RGBColor(0x8A, 0x8F, 0x96), RGBColor(0xFF, 0xFF, 0xFF)
GREEN, AMBER, RED = RGBColor(0x14, 0x6C, 0x2E), RGBColor(0x8A, 0x5A, 0x00), RGBColor(0xA1, 0x25, 0x1B)
GREEN_BG, AMBER_BG, RED_BG = RGBColor(0xDC, 0xF5, 0xE3), RGBColor(0xFF, 0xF4, 0xD6), RGBColor(0xFD, 0xE2, 0xE1)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def text(slide, x, y, w, h, content, size=14, bold=False, color=TEXT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    lines = content if isinstance(content, list) else [content]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run(); run.text = line
        run.font.size, run.font.bold, run.font.color.rgb = Pt(size), bold, color
    return tb


def bullets(slide, x, y, w, h, items, size=14):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        sub = item.startswith("  ")
        r = p.add_run(); r.text = ("– " if sub else "• ") + item.strip()
        r.font.size = Pt(size - 2 if sub else size); r.font.color.rgb = TEXT
        p.level = 1 if sub else 0; p.space_after = Pt(4)
    return tb


def box(slide, x, y, w, h, label, fill=LIGHT, line=NAVY, color=NAVY, size=11, bold=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.color.rgb = line; s.line.width = Pt(1.25)
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.05))
    for i, line_text in enumerate(label.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = line_text
        r.font.size = Pt(size if i == 0 else size - 2); r.font.bold = bold and i == 0
        r.font.color.rgb = color
    return s


def arrow(slide, x1, y1, x2, y2, color=NAVY, label=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(1.75)
    ln = c.line._get_or_add_ln()
    ln.append(etree.SubElement(ln, qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if label:
        text(slide, min(x1, x2) - 0.2, min(y1, y2) - 0.32, abs(x2 - x1) + 0.4, 0.3, label, size=9, color=GREY, align=PP_ALIGN.CENTER)


def header(slide, title, subtitle=None):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    text(slide, 0.5, 0.3, 10.5, 0.7, title, size=28, bold=True, color=NAVY)
    if subtitle:
        text(slide, 0.5, 0.95, 11.5, 0.45, subtitle, size=14, color=ORANGE)
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.4), Inches(12.33), Inches(0.03))
    rule.fill.solid(); rule.fill.fore_color.rgb = ORANGE; rule.line.fill.background()
    slide.shapes.add_picture(D + "logo.png", Inches(11.35), Inches(0.32), height=Inches(0.45))
    text(slide, 0.5, 7.05, 12.3, 0.3, "Royal Table · Account Growth Agent · Kiro Workshop Day 1 · 19 Nov 2026",
         size=9, color=GREY)


def picture(slide, path, x, y, max_w, max_h):
    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w * scale), Inches(h * scale))
    pic.line.color.rgb = RGBColor(0xCE, 0xCE, 0xCE); pic.line.width = Pt(0.75)
    return pic


def table(slide, x, y, w, rows, col_w, size=11, status_col=None):
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(0.3 * len(rows))).table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j); cell.text = val
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            p = cell.text_frame.paragraphs[0]; f = p.runs[0].font
            f.size = Pt(size); f.color.rgb = WHITE if i == 0 else TEXT; f.bold = i == 0
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY if i == 0 else (LIGHT if i % 2 else WHITE)
            if i and status_col is not None and j == status_col:
                fg, bg = {"Done": (GREEN, GREEN_BG), "Partial": (AMBER, AMBER_BG), "Gap": (RED, RED_BG)}.get(val, (TEXT, WHITE))
                f.color.rgb = fg; f.bold = True; cell.fill.fore_color.rgb = bg
    return t


# Logo as PNG for the slides (python-pptx does not embed SVG)
Image.open(D + "s0_start.png").crop((163, 88, 368, 137)).save(D + "logo.png")

# 1. Title ---------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
stripe = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(4.9), prs.slide_width, Inches(0.08))
stripe.fill.solid(); stripe.fill.fore_color.rgb = ORANGE; stripe.line.fill.background()
s.shapes.add_picture(D + "logo.png", Inches(0.8), Inches(0.8), height=Inches(0.8))
text(s, 0.8, 2.1, 11, 1.0, "Royal Table", size=54, bold=True, color=WHITE)
text(s, 0.8, 3.1, 11, 0.6, "Account Growth Agent", size=28, color=ORANGE)
text(s, 0.8, 3.8, 11, 0.6, "Who earns a seat at the Royal table", size=20, color=WHITE)
text(s, 0.8, 5.3, 11.5, 1.2, ["Kiro Workshop Day 1 · hackathon outcome · 19 November 2026",
                              "Streamlit + Amazon Bedrock agent with human approval, built spec-first with Kiro"],
     size=16, color=WHITE)

# 2. Problem and who ------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Why and who", "Every event spend decision starts with a target list nobody trusts")
bullets(s, 0.6, 1.7, 6.0, 4.8, [
    "Today: the Tampa Bay target list is picked by brand size",
    "  The budget gets argued over and the list goes through weeks of revisions",
    "  Nobody is confident in the final decision",
    "Royal Table scores every account on readiness to buy",
    "  explains each result in plain executive language",
    "  builds the invite list and drafts the spend request",
    "  a person must approve or reject it, with a reason",
    "Goal: grow existing Royal Cyber accounts by putting the right executives in the room",
], size=16)
box(s, 7.1, 1.8, 5.6, 1.3, "Account Manager (primary user)\nDecides who to invite and why, sets room and budget, approves the spend", size=14)
box(s, 7.1, 3.3, 5.6, 1.1, "Marketing\nRuns the campaign from the confirmed table", size=14, fill=WHITE)
box(s, 7.1, 4.6, 5.6, 1.5, "Data: 20 Tampa Bay financial services accounts\nIllustrative signals only, titles never names\n(data/tampa_target_accounts.csv)", size=13, fill=WHITE, line=ORANGE, color=TEXT)

# 3. What we built -------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "What we built", "One screen: set the table, run the agent, review, confirm")
picture(s, D + "s0_start.png", 0.5, 1.6, 6.6, 5.3)
table(s, 7.4, 1.7, 5.4, [
    ["App part", "Royal Table language"],
    ["Room size, invite list", "Seats at the table"],
    ["Score, reason codes", "Earning a seat"],
    ["⭐ Highly recommended (90+)", "Head of the table"],
    ["Spend request", "Cost of the table / per seat"],
    ["Approve or Reject", "Confirm the table"],
    ["Decision log", "Who set the table, and why"],
], [2.6, 2.8], size=12)
bullets(s, 7.4, 4.25, 5.4, 2.6, [
    "Score 0–100 from 6 weighted signals, tiers Invite / Nurture / Deprioritize",
    "Executive reason codes: Local decision maker, C-suite in the room, New CDO in first 100 days, Regulator deadline",
    "Decision board: counts, room fill, top-pick cards, score chart",
], size=13)

# 4. Architecture --------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Architecture", "Runtime path in the workshop environment (us-east-1)")
row_y, bw, bh = 1.9, 1.85, 0.95
xs = [0.45, 2.55, 4.65, 6.75, 8.85, 10.95]
labels = [
    "Browser\nAccount Manager",
    "CloudFront\n<id>.cloudfront.net",
    "nginx :80\nIDE host",
    "code-server :8080\nlogin, /absproxy/",
    "Vite :5173\nallowedHosts · base\nproxy /curator (ws)",
    "Streamlit :8501\napp.py UI + agent loop",
]
for x, lbl in zip(xs, labels):
    box(s, x, row_y, bw, bh, lbl, size=11)
for a, b in zip(xs, xs[1:]):
    arrow(s, a + bw, row_y + bh / 2, b, row_y + bh / 2)
text(s, 0.45, 1.5, 12, 0.3, "HTTPS + websocket, one forwarded port (5173). No extra ports opened.", size=11, color=GREY)

app_x = xs[5] + bw / 2
box(s, 8.6, 3.75, 2.0, 0.85, "tools.py\npure functions", size=11, fill=WHITE)
box(s, 10.85, 3.75, 2.05, 0.85, "Session state\nin memory only", size=11, fill=WHITE)
box(s, 8.6, 5.0, 2.0, 0.85, "data/*.csv\nassets/logo.svg", size=11, fill=WHITE)
arrow(s, app_x - 0.4, row_y + bh, 9.6, 3.75, label=None)
arrow(s, app_x + 0.2, row_y + bh, 11.85, 3.75)
arrow(s, 9.6, 4.6, 9.6, 5.0)

box(s, 3.2, 3.75, 3.4, 1.05, "Amazon Bedrock\nConverse API + tool use\nClaude Haiku 4.5 (inference profile)", size=12, fill=NAVY, color=WHITE, line=NAVY)
arrow(s, app_x - 0.7, row_y + bh, 6.6, 4.25, color=ORANGE)
text(s, 6.4, 3.25, 2.4, 0.4, "boto3 · BEDROCK_MODEL_ID · AWS_REGION", size=9, color=ORANGE)
box(s, 0.45, 3.75, 2.4, 1.05, "IAM instance role\nworkshop instance role\n(no keys in code)", size=11, fill=WHITE, line=ORANGE, color=TEXT)
arrow(s, 2.85, 4.27, 3.2, 4.27, color=ORANGE)
box(s, 3.2, 5.2, 3.4, 0.85, "CloudWatch AWS/Bedrock\ninvocations, latency, throttles", size=11, fill=WHITE)
arrow(s, 4.9, 4.8, 4.9, 5.2, color=GREY)
box(s, 0.45, 5.2, 2.4, 0.85, "JSON logs (stderr)\nrun · bedrock_call · tool_call", size=11, fill=WHITE)
text(s, 0.45, 6.25, 12.4, 0.6,
     "Separate in the same repo: React + Vite scoring prototype at /absproxy/5173/ (browser only, no AI calls).",
     size=11, color=GREY)

# 5. Agent loop and runtime gates ----------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Agent loop and runtime gates", "The model chooses tool calls; numbers and status changes are outside its control")
steps = [("Set the table", "budget · room size"), ("score_accounts", "20 scored, tiers, codes"),
         ("build_invite_list", "Invite tier until room full"), ("draft_spend_request", "always Pending Approval"),
         ("HUMAN GATE", "Approve / Reject + reason"), ("Marketing", "runs the campaign")]
x = 0.45
for i, (t1, t2) in enumerate(steps):
    gate = t1 == "HUMAN GATE"
    box(s, x, 1.9, 1.95, 1.1, f"{t1}\n{t2}", size=12, fill=ORANGE if gate else (NAVY if 0 < i < 4 else LIGHT),
        color=WHITE if (gate or 0 < i < 4) else NAVY, line=ORANGE if gate else NAVY, shape=MSO_SHAPE.CHEVRON if 0 < i < 4 else MSO_SHAPE.ROUNDED_RECTANGLE)
    if i < len(steps) - 1:
        arrow(s, x + 1.95, 2.45, x + 2.1, 2.45)
    x += 2.1
text(s, 2.55, 3.05, 6.3, 0.35, "Bedrock Converse tool-use loop (max 6 turns)", size=11, color=ORANGE, align=PP_ALIGN.CENTER)
table(s, 0.45, 3.6, 12.4, [
    ["Gate", "How it is enforced", "Evidence"],
    ["Numbers only from tools", "Model passes small args; app supplies data; UI budget/room override the model", "Mock model asked room 999, budget 1 → app used 40 and 25,000"],
    ["Only a person changes status", "Approve/Reject are UI handlers, not tools; tool has no status parameter", "Request stays Pending Approval until a click"],
    ["Reason required", "Empty reason → error, status unchanged", "Browser test + mocked test"],
    ["Bounded run", "6-turn cap; run valid only if draft_spend_request was called", "Worst-case scenario: no request, no buttons"],
    ["Safe rendering", "CSV values html.escape'd before HTML rendering", "Injection test: <img onerror> rendered as text"],
    ["Config fails closed", "Missing BEDROCK_MODEL_ID / AWS_REGION → error, no AWS call", "Logged as config_error"],
], [2.6, 5.6, 4.2], size=11)

# 6. Delivery lifecycle gates --------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "How it was built: spec-first with gates", "Every feature came from a document a person reviewed")
flow = [("Steering", "product · tech · structure\ncode-style (fileMatch)"), ("Requirements", "EARS, 13 reqs\nAPPROVED"),
        ("Design", "tools · loop · state\nAPPROVED"), ("Tasks", "9 tasks\nticked"), ("Build", "tools.py · app.py"),
        ("Tests", "pytest 7 · Playwright 4\nVitest 25"), ("Scans", "pip-audit · bandit\nnpm audit · secrets")]
x = 0.45
for i, (t1, t2) in enumerate(flow):
    approved = "APPROVED" in t2
    box(s, x, 1.85, 1.6, 1.15, f"{t1}\n{t2}", size=12, fill=ORANGE if approved else LIGHT,
        color=WHITE if approved else NAVY, line=ORANGE if approved else NAVY)
    if i < len(flow) - 1:
        arrow(s, x + 1.6, 2.42, x + 1.78, 2.42)
    x += 1.78
bullets(s, 0.6, 3.35, 6.1, 3.5, [
    "Human gates: requirements and design approved before code; spec changes made only on request and marked in the docs",
    "Automated gates: unit tests, browser tests against real Bedrock, security scan",
    "Kiro hook: security-scan runs on save of app.py, tools.py, requirements*.txt, package.json (shell command, no credits)",
    "Kiro permission rule blocked the agent from writing .kiro/settings/ → MCP config handed to the user",
], size=13)
table(s, 7.0, 3.4, 5.8, [
    ["Check", "Result"],
    ["pytest (scoring, invite, cost)", "7 passed"],
    ["Playwright browser tests", "4 passed (~30 s)"],
    ["Vitest (React scoring)", "25 passed"],
    ["pip-audit / npm audit", "0 vulnerabilities"],
    ["bandit / detect-secrets", "0 issues / 0 secrets"],
], [3.4, 2.4], size=12)

# 6b. AI-DLC agents -------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "AI-DLC with four agents", "Three roles plus a read-only conductor. You own every gate.")
box(s, 4.4, 1.6, 4.5, 0.75, "orchestrator · read-only\n\"where are we, who's next, what to paste\"", size=12, fill=WHITE, line=GREY, color=TEXT)
lane = [("docs/brd-*.md", "brief", LIGHT, NAVY), ("spec", "writes .kiro/specs only", NAVY, WHITE),
        ("YOU", "approve req + design", ORANGE, WHITE), ("build", "branch · test + commit per task", NAVY, WHITE),
        ("checks", "pytest · scan · lint", LIGHT, NAVY), ("reviewer", "read-only · file:line", NAVY, WHITE),
        ("YOU", "fix + merge", ORANGE, WHITE)]
x = 0.45
for i, (t1, t2, fill, col) in enumerate(lane):
    box(s, x, 2.75, 1.62, 1.0, f"{t1}\n{t2}", size=12, fill=fill, color=col, line=ORANGE if t1 == "YOU" else NAVY)
    if i < len(lane) - 1:
        arrow(s, x + 1.62, 3.25, x + 1.78, 3.25)
    x += 1.78
for gx in (1.25, 4.8, 7.05, 10.6):
    arrow(s, 6.65, 2.35, gx + 0.55, 2.75, color=GREY)
table(s, 0.45, 4.1, 12.4, [
    ["Agent", "Allowed", "Blocked by a permission rule", "Model"],
    ["orchestrator", "read; git status/log/branch/diff, ls, cat, grep", "all writes; every other shell command", "Auto (default)"],
    ["spec", "write .kiro/specs/** and docs/brd-*.md", "writes anywhere else (app code, tests, config)", "Auto (default)"],
    ["build", "read, write, pytest, git add/commit, new branch", "git push / merge / rebase / reset --hard / branch -D, checkout main", "claude-sonnet-4.6"],
    ["reviewer", "read; git diff/log/show, pytest, security-scan, npm lint/build/test", "all writes; every other shell command", "claude-sonnet-4.6"],
], [1.6, 4.4, 4.7, 1.7], size=11)
text(s, 0.45, 6.25, 12.4, 0.7, ["Files: .kiro/agents/{orchestrator,spec,build,reviewer}.md · steering loaded via file://.kiro/steering/**/*.md · git-workflow.md sets <type>/<slug> + Conventional Commits.",
     "Example run (docs/ai-dlc-agents.md): explain why no request was drafted in the worst-case scenario. Guardrail test: reviewer + \"echo guardrail-test\" must be blocked."], size=11, color=GREY)

# 7. Dependencies --------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Dependencies", "Pinned to tested versions; nothing hard-coded")
table(s, 0.45, 1.7, 12.4, [
    ["Layer", "Component", "Version / ID", "Notes"],
    ["Runtime (Python 3.11)", "streamlit · boto3", "1.67.0 · 1.44.7", "requirements.txt (pinned); Altair 6.3 ships with Streamlit"],
    ["Test", "pytest · pytest-playwright · playwright", "9.2.0 · 0.10.0 · 1.65.2", "requirements-dev.txt; Chromium headless 1255"],
    ["AI", "Amazon Bedrock Converse API", "us.anthropic.claude-haiku-4-5-20251001-v1:0", "Also tested: Sonnet 4.5, Nova Pro"],
    ["AWS", "IAM instance role · CloudWatch", "workshop instance role · AWS/Bedrock", "Default credential chain, us-east-1 only"],
    ["Front door", "CloudFront → nginx → code-server → Vite", "Vite 8, React 19, TS 7", "vite.config.ts proxies /curator to :8501"],
    ["OS packages", "libatomic, nss, atk, mesa-libgbm, alsa-lib, noto emoji", "dnf (Amazon Linux 2023)", "playwright --with-deps unsupported on AL2023"],
    ["Dev tooling", "uvx: pip-audit, bandit, detect-secrets", "latest at scan time", "scripts/security-scan.sh, no project deps added"],
    ["Kiro", "Steering 5 · spec 1 · hook 1 · aws-mcp (user)", "Playwright MCP + AWS Pricing MCP", "MCP configs tested over stdio; user pastes mcp.json"],
], [2.0, 3.6, 3.4, 3.4], size=11)

# 8–10. Scenarios -------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Scenario 1 · best case: decision board", "Defaults: budget $25,000, room of 40 executives")
picture(s, D + "s1_board.png", 0.45, 1.6, 8.3, 5.35)
bullets(s, 8.95, 1.7, 4.0, 5.2, [
    "20 accounts scored, 7 Invite tier",
    "4 highly recommended: Suncoast 100, BayFirst 97, Raymond James 92, GTE 90",
    "Room fill 14 / 40",
    "All four top picks: local decision maker + C-suite in the room",
    "Run: 4 Bedrock turns, 5.0 s, 12,022 input / 501 output tokens",
], size=14)

s = prs.slides.add_slide(BLANK)
header(s, "Scenario 1 · best case: spend request → approved", "Pending Approval until a person confirms the table")
picture(s, D + "s1_request.png", 0.45, 1.6, 6.15, 4.6)
picture(s, D + "s1_approved_log.png", 6.75, 1.6, 6.15, 4.6)
text(s, 0.45, 6.3, 6.2, 0.6, "Before: 7 accounts · 14 executives · $25,000 · $1,786 per seat · Approve / Reject shown", size=12)
text(s, 6.75, 6.3, 6.2, 0.6, "After: status Approved, buttons gone, log shows one Agent and one Human entry", size=12)

s = prs.slides.add_slide(BLANK)
header(s, "Scenario 2 · worst case: no seat can be filled", "Room size 1: every Invite account needs 2 seats")
picture(s, D + "s2_error.png", 0.45, 1.6, 7.6, 5.35)
bullets(s, 8.3, 1.7, 4.6, 5.2, [
    "Invite list is empty: room fill 0 / 1",
    "Agent ended without drafting a request (3 turns, 3.0 s, 6,482 / 246 tokens)",
    "App fails safe: \"Agent did not draft a spend request.\"",
    "No Approve / Reject buttons, nothing to approve",
    "Logged: run_end outcome=no_request (WARNING)",
    "Gap: message doesn't say why. Next: \"No Invite account fits a room of 1 (smallest needs 2)\"",
], size=14)

# 11. Scorecard ----------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Hackathon scorecard", "Against the Day 1 lab guide checklists (best effort)")
rows = [
    ["Lab", "Checklist item", "Status", "Evidence / note"],
    ["1", "App runs via /absproxy/5173/", "Done", "Root cause explained first; allowedHosts pinned to exact host (guide: '.cloudfront.net')"],
    ["1", "Steering saved, read and edited", "Partial", "6 files incl. code-style fileMatch and git-workflow (MUST/NEVER); no testing / verify-first; your own edit not confirmed"],
    ["1", "Feature built from a reviewed spec", "Done", "requirements → design → tasks with approval stops (brief kept in steering, not docs/brd-*.md)"],
    ["1", "A hook runs on save", "Done", "security-scan PostFileSave hook (not lint)"],
    ["1–3", "Work committed", "Gap", "Only the template commit; everything else uncommitted"],
    ["2", "Skill installed from GitHub · review in skill format · skill fixed", "Gap", "No skill-creator, no code-review skill"],
    ["2", "Checks: linter, secrets, static scan", "Partial", "oxlint, detect-secrets, bandit, pip-audit, npm audit; not gitleaks/semgrep or npm scripts"],
    ["2", "Screenshot from a real browser", "Done", "Playwright tests + scenario screenshots; Playwright MCP verified, mcp.json paste pending"],
    ["3", "Three agents (spec, build, reviewer)", "Partial", "spec, build, reviewer + orchestrator created with permission rules; you still read the reviewer and run the guardrail test"],
    ["3", "A spec you approved", "Done", "Target Curator / Royal Table spec, 13 requirements"],
    ["3", "Tests on a branch + reviewer findings", "Partial", "Tests pass on main work; branch + one reviewer pass scripted in docs/ai-dlc-agents.md"],
    ["3", "A person merged it", "Gap", "Ready once the build agent's branch exists"],
]
table(s, 0.45, 1.55, 12.4, rows, [0.5, 3.9, 0.9, 7.1], size=9, status_col=2)
box(s, 0.45, 6.05, 3.9, 0.9, "Lab checklists: 50 / 100\nDone 1 · Partial 0.5 · Gap 0 → 7 of 14", size=13, fill=AMBER_BG, line=AMBER, color=AMBER)
box(s, 4.7, 6.05, 3.9, 0.9, "Product vs its own spec: 95 / 100\nAll success criteria met; summary > 3 sentences", size=13, fill=GREEN_BG, line=GREEN, color=GREEN)
box(s, 8.95, 6.05, 3.9, 0.9, "Overall (50 / 50): ≈ 72 / 100\nAgents in place; run Lab 3 to close", size=13, fill=LIGHT, line=NAVY, color=NAVY)

# 12. Beyond the guide ---------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Beyond the guide", "Delivered in addition to the lab checklists")
bullets(s, 0.6, 1.7, 6.0, 5.2, [
    "Real Amazon Bedrock agent with tool use and a human approval gate",
    "Executive reason codes and Royal Table naming, mapped to every UI section",
    "Royal Cyber branding from royalcyber.com (logo, #003963 / #E66208)",
    "Decision board: information radiator with top picks and score chart",
    "Playwright browser tests against real Bedrock, with screenshots",
    "Structured logging: latency and tokens per Bedrock call",
    "Security scan script + Kiro hook; pinned dependencies; HTML escaping",
    "README: run, proxy, scoring rules, troubleshooting, MCP config",
], size=15)
table(s, 7.0, 1.8, 5.8, [
    ["Account rule (lab guide)", "Status"],
    ["us-east-1 only", "Done"],
    ["Test data only", "Done"],
    ["Bedrock under 1 request / second", "Done"],
    ["No Kiro API key printed or committed", "Done"],
], [4.0, 1.8], size=12, status_col=1)
text(s, 7.0, 4.0, 5.8, 1.6, ["Sequential calls only: a run makes 3–4 calls over 3–5 s.",
                             "Sample uses real company names with illustrative signals, labelled as such."], size=12, color=GREY)

# 13. Gaps and next steps ------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, "Gaps and next steps", "Ordered by value per Kiro credit")
table(s, 0.45, 1.7, 12.4, [
    ["#", "Next step", "Kiro credits", "Closes"],
    ["1", "git add -A && git commit (in a terminal, yourself)", "0", "Commit gap; unblocks Lab 3 branch"],
    ["2", "Paste the tested .kiro/settings/mcp.json (Playwright + Pricing)", "0", "Lab 2 MCP item"],
    ["3", "Widen allowedHosts to ['.cloudfront.net'] as the guide recommends", "Low", "Lab 1 config note"],
    ["4", "Worst-case message: say why no request was drafted", "Low", "Scenario 2 gap"],
    ["5", "Install skill-creator, write and refine a code-review skill", "Medium", "Lab 2 skill items"],
    ["6", "testing and verify-first steering (git-workflow done)", "Low", "Lab 1 steering"],
    ["7", "Run the agent flow in docs/ai-dlc-agents.md: spec → build branch → one review → you merge", "Highest", "Remaining Lab 3 items"],
    ["8", "Try Sonnet 4.5 for the three-sentence summary (compare with Pricing MCP)", "Low", "Last product criterion"],
], [0.5, 7.1, 1.6, 3.2], size=12)
text(s, 0.45, 5.0, 12.4, 1.8, [
    "Credits: the lab guide measured about 38 credits for Lab 1 on Auto; check the status bar (Kiro Pro <used> / 1000).",
    "Kept low here: Auto model, scripted checks, one browser run per scenario, deck generated by a script.",
    "Bedrock usage per run (tokens, from app logs): best case 12,022 in / 501 out · worst case 6,482 in / 246 out.",
], size=13, color=TEXT)

prs.save("docs/royal-table-hackathon.pptx")
print("slides:", len(prs.slides))
