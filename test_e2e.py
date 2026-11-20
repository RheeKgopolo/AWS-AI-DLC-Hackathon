"""Browser tests for Royal Table, run against real Amazon Bedrock (option 1).

Run:
    BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0 AWS_REGION=us-east-1 \
    .venv/bin/pytest test_e2e.py --screenshot only-on-failure --output test-results

Skipped automatically when BEDROCK_MODEL_ID or AWS_REGION is not set, so a plain
`pytest` run still only needs the unit tests. Assertions check numbers that come
from the tools, never the agent's wording, because the model's text varies.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

PORT = 8599  # separate from the live app on 8501
BASE_URL = f"http://127.0.0.1:{PORT}/"
AGENT_TIMEOUT = 120_000  # ms; a real Bedrock run takes roughly 10 to 30 seconds
SHOTS = Path("test-results")

pytestmark = pytest.mark.skipif(
    not (os.environ.get("BEDROCK_MODEL_ID") and os.environ.get("AWS_REGION")),
    reason="BEDROCK_MODEL_ID and AWS_REGION are required for browser tests",
)


@pytest.fixture(scope="session")
def app_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(PORT), "--server.address", "127.0.0.1",
         "--server.headless", "true", "--browser.gatherUsageStats", "false"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if urllib.request.urlopen(BASE_URL + "_stcore/health", timeout=2).status == 200:
                break
        except OSError:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Streamlit did not start")
    yield BASE_URL
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture
def app(page: Page, app_server) -> Page:
    page.set_viewport_size({"width": 1366, "height": 900})
    page.goto(app_server)
    expect(page.get_by_role("button", name="Run agent")).to_be_visible(timeout=30_000)
    return page


def status(page: Page):
    # The status pill. The agent's own text may also mention the status, so never match on text alone.
    return page.locator(".pill")


def run_agent(page: Page):
    page.get_by_role("button", name="Run agent").click()
    expect(status(page)).to_have_text("Pending Approval", timeout=AGENT_TIMEOUT)


def metric(page: Page, label: str):
    return page.get_by_test_id("stMetric").filter(has_text=label).get_by_test_id("stMetricValue")


def set_reason(page: Page, text: str):
    box = page.get_by_label("Reason (required)")
    box.fill(text)
    box.press("Enter")  # Streamlit commits text inputs on Enter or blur
    page.wait_for_timeout(500)


def shoot(page: Page, name: str):
    """Whole-page screenshot. Streamlit scrolls inside its own container, so
    full_page=True misses most of the app; a tall viewport captures all of it."""
    SHOTS.mkdir(exist_ok=True)
    page.set_viewport_size({"width": 1366, "height": 3600})
    page.wait_for_timeout(1500)  # let tables and the chart redraw at the new size
    page.screenshot(path=str(SHOTS / name))


def test_header_logo_is_fully_visible(app: Page):
    logo = app.get_by_alt_text("Royal Cyber")
    expect(logo).to_be_visible()
    expect(app.get_by_text("Royal Table", exact=False).first).to_be_visible()
    # The logo must sit below Streamlit's fixed toolbar (the earlier "logo is cut" bug).
    toolbar = app.get_by_test_id("stHeader").bounding_box()
    box = logo.bounding_box()
    assert box["height"] > 30
    assert box["y"] >= toolbar["y"] + toolbar["height"]
    SHOTS.mkdir(exist_ok=True)
    app.screenshot(path=str(SHOTS / "01-start.png"))


def test_run_shows_decision_board_and_pending_request(app: Page):
    run_agent(app)

    expect(metric(app, "Accounts scored")).to_have_text("20")
    expect(metric(app, "Invite tier")).to_have_text("7")
    expect(metric(app, "Highly recommended")).to_have_text("4")
    expect(metric(app, "Room fill")).to_have_text("14 / 40")
    expect(app.get_by_text("HIGHLY RECOMMENDED", exact=True)).to_have_count(4)
    for company in ("Suncoast Credit Union", "BayFirst Financial", "Raymond James", "GTE Financial"):
        expect(app.locator(".card", has_text=company)).to_be_visible()
    expect(app.locator('[data-testid="stVegaLiteChart"], .vega-embed').first).to_be_visible()

    expect(metric(app, "Executives")).to_have_text("14")
    expect(metric(app, "Cost per executive")).to_have_text("$1,786")
    expect(app.get_by_role("button", name="Approve")).to_be_visible()
    expect(app.get_by_role("button", name="Reject")).to_be_visible()

    tool_calls = app.get_by_text("Agent tool calls", exact=False)
    tool_calls.click()
    for name in ("score_accounts", "build_invite_list", "draft_spend_request"):
        expect(app.get_by_text(name, exact=True).first).to_be_visible()

    shoot(app, "02-decision-board.png")


def test_approve_needs_reason_then_logs_human_decision(app: Page):
    run_agent(app)

    app.get_by_role("button", name="Approve").click()
    expect(app.get_by_text("A reason is required.")).to_be_visible()
    expect(status(app)).to_have_text("Pending Approval")

    set_reason(app, "Strong local decision makers")
    app.get_by_role("button", name="Approve").click()
    expect(status(app)).to_have_text("Approved")
    expect(app.get_by_role("button", name="Approve")).to_have_count(0)
    expect(app.get_by_role("button", name="Reject")).to_have_count(0)

    log = app.get_by_test_id("stDataFrame").last
    expect(log).to_contain_text("Agent")
    expect(log).to_contain_text("Human")
    shoot(app, "03-approved.png")


def test_reject_with_reason(app: Page):
    run_agent(app)
    set_reason(app, "Budget not confirmed")
    app.get_by_role("button", name="Reject").click()
    expect(status(app)).to_have_text("Rejected")
    expect(app.get_by_role("button", name="Approve")).to_have_count(0)
