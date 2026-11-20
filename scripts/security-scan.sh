#!/usr/bin/env bash
# Security scans for Royal Table. Runs scanners through uvx and npm, so no project
# dependencies are added. Exits non-zero if any scanner reports a problem.
#   bash scripts/security-scan.sh
set -u
cd "$(dirname "$0")/.."
fail=0
run() {
  local name="$1"; shift
  if "$@" >/tmp/royal-table-scan.log 2>&1; then
    echo "PASS  $name"
  else
    echo "FAIL  $name"; sed 's/^/      /' /tmp/royal-table-scan.log | tail -20; fail=1
  fi
}

run "pip-audit (Python dependencies)" uvx --python 3.11 pip-audit -r requirements-dev.txt
run "bandit (Python code)"            uvx bandit -q -r app.py tools.py
run "npm audit (JS dependencies)"     npm audit --audit-level=high
run "detect-secrets (whole repo)"     bash -c '
  uvx detect-secrets scan --exclude-files "node_modules|\.venv|package-lock\.json|dist|test-results|\.playwright-mcp" . |
  python3 -c "import json,sys; r=json.load(sys.stdin)[\"results\"]; n=sum(map(len,r.values())); [print(f,[x[\"type\"] for x in v]) for f,v in r.items()]; sys.exit(1 if n else 0)"'

exit $fail
