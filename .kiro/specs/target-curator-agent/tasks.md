# Tasks: Royal Table · Account Growth Agent

- [x] 1. Project setup: create `requirements.txt` (`streamlit`, `boto3`, `pytest`), a `.venv`, and install. Ignore `.venv` and `__pycache__` in git.
- [x] 2. `tools.py`: `load_accounts`, `score_accounts`, `build_invite_list`, `draft_spend_request` as pure functions (requirements 1 to 7).
- [x] 3. `test_tools.py`: assertions from the success criteria (four named scores, invite lists for room sizes 40 and 10, $1,786 cost per executive). Run `pytest` and fix `tools.py` until all pass. Never change the tests or the data.
- [x] 4. `app.py` UI: budget input (25000), room size input (40), Run agent button, scored accounts table, tool call display, spend request display (requirement 10).
- [x] 5. `app.py` Bedrock agent loop: Converse API with tool use, dispatcher, environment variable checks, system prompt (requirements 8 and 9).
- [x] 6. `app.py` approval buttons and log: Approve and Reject with a required reason, and the Agent and Human log entries (requirements 11 and 12).
- [x] 7. Final check: `pytest` passes, `python -m py_compile app.py tools.py`, and the Streamlit app starts without errors.
- [x] 8. Highly recommended flag in `tools.py` and the decision board in `app.py` (requirement 13).
- [x] 9. Playwright browser tests in `test_e2e.py` against real Bedrock, with `requirements-dev.txt`.
