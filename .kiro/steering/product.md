# Product

## Two features in this repo

1. **Account readiness scoring (React app).** Browser only, no backend, no AI calls. Everything below this section describes it.
2. **Royal Table (Account Growth Agent) (Python app).** A separate Streamlit app at the repo root that uses an Amazon Bedrock agent with three tools, and needs human approval of a spend request. Spec: `.kiro/specs/target-curator-agent/`. It is the only part of this repo that may call AWS or an LLM. The "no backend", "no AI calls" and "no network calls" rules below do not apply to it, and its out-of-scope list is in its own `requirements.md`. Do not mix code between the two apps.

The two share the same sample data (`data/` for Python, `public/sample/` for React). The files must stay identical.

---

## Account readiness scoring (React app)

The numbered requirements and full success criteria live in `feature-account-readiness-scoring.md` (include it in chat with `#feature-account-readiness-scoring`). That file is authoritative for requirement numbers. This file is the product-level summary, so update both together.

## Why

The Tampa Bay event target list is mined by brand size, so the budget gets argued over, the list goes through weeks of revisions, and nobody is confident in the final decision. The app scores every account on readiness to buy, explains each result in one sentence, and produces an invite list the team can agree on in one meeting. Budget is aligned only after the list is agreed.

## Who it is for

A sales leader or events lead at a B2B technology services firm who decides which financial services executives in Tampa Bay to invite to an executive event, and must defend that decision to leadership with a reason behind every invite and every dollar.

## In scope

- Load an accounts CSV (upload or bundled sample of 20 accounts).
- Score each account 0 to 100 from six weighted signals, with adjustable weights.
- Assign a tier (Invite, Nurture, Deprioritize), a one sentence "why now", and a movement badge against the original tier.
- Build an invite list capped by room size, flagging and excluding accounts outside Tampa Bay.
- Compute cost per qualified executive from an event budget.
- Keep a decision log of changes, and show what entered or left the invite list after each change.
- Print a one page decision summary and export the invite list as CSV.
- Validate input: missing or duplicate data is an error, unrecognized values are a visible warning.

## Out of scope

- CRM or any other system integration, backend, database, API, login or permissions.
- AI or LLM calls, web scraping, data enrichment, or any network call at runtime.
- Sending emails, invitations or calendar events.
- Individual names or contact details. Personas are job titles only.
- Multiple events or event comparison. One event, one budget.
- Charts, theming, multi language, mobile layout.
- Saving data between sessions. A refresh resets to the loaded file.
- Renaming the `idea-board` package in this feature.

## Requirements

Condensed. See the feature file for the exact numbered requirements (1 to 33).

- CSV with 13 named columns. A missing column, a duplicate company, a blank company or an empty file is an error and shows no results.
- Points per signal and default weights (authority 20, offering fit 25, triggers 20, deal size 15, warmth 10, persona confidence 10). The score is the weighted sum, scaled to total 100, rounded.
- Tiers: Invite at 70 and above, Nurture 40 to 69, Deprioritize below 40.
- Ties keep CSV order and are marked as tied.
- Invite list: Invite accounts in score order, Tampa Bay only, stopping at the first account that does not fit the room size (default 40). Each target_persona item is one executive.
- Cost per qualified executive is budget divided by invited executives, rounded to the nearest dollar. It shows "n/a" with no budget or no executives.
- Sliders from 0 to 50 update results within one second. One decision log entry per drag, recorded on release.
- Loading a new file resets all state, with confirmation if the log is not empty.
- A visible "Sample data, illustrative only" banner when the bundled sample is loaded.
- Keyboard-usable, labeled sliders.

## Success criteria

- Loading the sample shows 20 accounts sorted by score with tier, badge and why now.
- With default weights the sample produces the exact scores, tiers and badges asserted in `src/scoring.test.ts`. The invite list has 7 accounts and 14 executives at room size 40, and 5 accounts and 10 executives at room size 10.
- A budget of 40000 with 20 invited executives shows $2,000.
- Moving a slider reorders the table, adds one log entry, and the added and removed panel names the accounts that changed.
- The decision summary prints on one page for a normal list, and the exported CSV opens in Excel.
- Every edge case in requirements 20 to 33 of the feature file has a visible, specific message and not a silent failure.

## Constraints

- React with TypeScript on Vite. Plain CSS, no UI framework.
- PapaParse for CSV. No other runtime dependency without a clear need.
- Runs entirely in the browser, offline after install, all state in memory.
- Sample data at `public/sample/tampa_target_accounts.csv`, titles only. All signal values are illustrative assumptions, not research about real companies.
- Scoring is a single pure function with unit tests covering requirements 4 to 7.
- Runs with `npm install` and `npm run dev`, with no environment variables or keys.

## Open questions

- Whether to rename the package from `idea-board` to match the product.
- The source column in the sample says "Public company, illustrative signals" for credit unions, which are not public companies. The sample file is deliberately unchanged.
