---
inclusion: manual
---

# Account Readiness Scoring and Invite List

## Why

Our Tampa Bay event target list is mined by brand size, so the budget gets argued over, the list goes through weeks of revisions, and nobody is confident in the final decision. This feature scores every account on readiness to buy, explains each result in one sentence, and produces an invite list the team can agree on in one meeting. Budget is aligned only after the list is agreed.

## Who it is for

A sales leader or events lead at a B2B technology services firm who must decide which financial services executives in Tampa Bay to invite to an executive event, and defend that decision to leadership with a clear reason behind every invite and every dollar.

## In scope

* Load an accounts CSV, either uploaded by the user or the bundled sample file.

* Score each account from 0 to 100 using six weighted signals.

* Assign a curated tier of Invite, Nurture or Deprioritize to each account.

* Show a one sentence "why now" reason for each account.

* Compare the curated tier with the original tier and flag accounts that moved.

* Let the user adjust signal weights with sliders and see results update instantly.

* Build an invite list capped by room size.

* Calculate cost per qualified executive from an event budget.

* Keep a decision log of every weight change during the session.

* Show what changed in the invite list after each adjustment.

* Produce a printable one page decision summary.

* Export the invite list as CSV.

## Out of scope

* No CRM, Salesforce, HubSpot or any other system integration.

* No backend server, database or API of any kind.

* No calls to AI or LLM services. Reasons are generated from templates.

* No web scraping, data enrichment or external lookups.

* No user accounts, login or permissions.

* No sending of emails, invitations or calendar events.

* No storing individual people's names or contact details. Personas are job titles only.

* No event selection or comparison across multiple events. One event, one budget.

* No charts or charting libraries. Tables and simple badges only.

* No saving data between sessions. Refreshing the page resets to the loaded file.

* No multi language support, theming or mobile specific layout.

* No renaming of the `idea-board` package as part of this feature.

* No limit on the number of accounts, but no performance work beyond a 500 account file.

## Requirements

1. The app shall accept a CSV with these columns: company, segment, city, market, current_tier, local_decision_authority, offering_fit, trigger_signals, deal_size_fit, relationship_warmth, persona_confidence, target_persona, source.

2. The app shall provide a "Load sample data" button that loads a bundled file of 20 accounts without an upload.

3. If a required column is missing, the app shall show an error naming the missing column and shall not display results.

4. The app shall convert signal values to points as follows. local_decision_authority: Yes 3, Partial 2, No 0. offering_fit, deal_size_fit, persona_confidence: High 3, Medium 2, Low 1, blank 0. relationship_warmth: Warm 3, Known 2, Cold 0. trigger_signals: count of semicolon separated items, capped at 3.

5. The app shall use these default weights, totaling 100: local decision authority 20, offering fit 25, trigger signals 20, deal size fit 15, relationship warmth 10, persona confidence 10.

6. The score shall equal the sum of (weight multiplied by points divided by 3) across all six signals, rounded to a whole number between 0 and 100.

7. The curated tier shall be Invite for scores 70 and above, Nurture for 40 to 69 and Deprioritize below 40.

8. Each account shall show a "why now" sentence built from its two highest contributing signals, for example "Strong offering fit and active trigger signals: new CDO; cloud migration."

9. Each account shall show a movement badge comparing current_tier to curated tier, where Tier 1 maps to Invite, Tier 2 to Nurture and Tier 3 to Deprioritize. Badges are Moved up, Moved down or No change.

10. The results table shall be sorted by score, highest first, and show company, segment, city, score, curated tier, movement badge and why now.

11. Each of the six weights shall have a slider from 0 to 50. When any slider changes, all scores, tiers and the table shall update within one second without a page reload.

12. The app shall show the current total of all weights and recalculate scores proportionally when the total is not 100.

13. The user shall be able to set a room size, defaulting to 40. Each item in target_persona (semicolon separated) counts as one invited executive.

14. The invite list shall include Invite tier accounts in score order until adding the next account would exceed the room size.

15. The user shall be able to enter an event budget in US dollars. The app shall display cost per qualified executive as budget divided by the number of invited executives, rounded to the nearest dollar.

16. Every slider change shall add a decision log entry with timestamp, signal name, old weight, new weight, and the number of accounts whose tier changed. The user may add an optional reason note to each entry.

17. After each change, the app shall show which accounts were added to and removed from the invite list compared with the previous state.

18. A "Decision summary" view shall show, on one printable page, the current weights, room size, budget, cost per qualified executive, and each invited account with score, persona titles and why now.

19. An "Export CSV" button shall download the invite list with columns company, segment, score, curated_tier, why_now, target_persona.

### Edge cases (added after interview, all answers are defaults unless noted)

20. Data loading. If two rows share a company name (case-insensitive), the app shall show an error naming the company and shall not display results. If a file has no data rows, the app shall show an error and no results. Extra columns shall be ignored, headers shall match case-insensitively, and a UTF-8 BOM shall be accepted.

21. Blank or invalid cells. A blank company shall be an error naming the row. A blank target_persona shall count as 0 executives and show a warning. An unrecognized value in a signal column or current_tier shall score 0 (current_tier shows No change) and show a warning naming the row and column, never a silent 0.

22. Triggers. trigger_signals items shall be trimmed, matched case-insensitively and counted once each, then capped at 3.

23. Scoring boundaries. A score of exactly 70 is Invite and exactly 40 is Nurture. If all weights are 0, the app shall show "Set at least one weight above 0" and no scores.

24. Ties. Accounts with the same score shall keep CSV order and be marked as tied.

25. Market. Accounts whose market is not "Tampa Bay" shall be flagged in the table and excluded from the invite list, but still scored.

26. Invite list stops at the first account that does not fit (requirement 14). If an Invite account has more executives than the whole room size, the app shall show a message naming it and saying it cannot fit.

27. Inputs. Room size shall accept whole numbers of 1 or more only. Budget shall accept digits, commas and a leading $, reject negatives, and treat blank as "no budget entered". When there are 0 invited executives or no budget, cost per qualified executive shall show "n/a".

28. Decision log. One entry per slider drag, recorded on release. Moving a slider back creates another entry. Changes to room size and budget shall also be logged and labeled as such.

29. Added and removed panel. It shall compare against the state before the most recent change only.

30. Loading a new file or the sample shall reset weights, room size, budget, the decision log and the added and removed panel. If the log is not empty, the app shall ask for confirmation first.

31. When the bundled sample is loaded, the app shall show a visible "Sample data, illustrative only" banner.

32. If the invite list is empty, "Export CSV" and the Decision summary shall be disabled with a message. The printable summary may run to a second page if the list is long. Exported CSV shall have a header row, quote fields containing commas, include a UTF-8 BOM, and be named invite_list.csv.

33. Accessibility. Sliders shall have visible labels and be usable with the keyboard.

## Success criteria

* Clicking "Load sample data" shows a table of 20 accounts sorted by score, each with a score, tier, badge and why now sentence.

* Uploading a CSV missing the persona_confidence column shows an error naming persona_confidence.

* At least one sample account shows Moved up and at least one shows Moved down.

* Dragging the offering fit slider to 0 visibly reorders the table and adds a decision log entry.

* Setting room size to 10 shrinks the invite list so the total of persona titles is 10 or fewer.

* Entering a budget of 40000 with 20 invited executives shows a cost per qualified executive of $2,000.

* After a slider change, the added and removed panel names the accounts that entered or left the invite list.

* The Decision summary view prints on one page from the browser's print dialog.

* The exported CSV opens in Excel with the six listed columns and one row per invited account.

* A CSV with two rows named the same company shows an error naming that company.

* A CSV with an unrecognized offering_fit value shows a warning naming the row and column, and that account scores 0 for the signal.

* Setting all six weights to 0 shows "Set at least one weight above 0" and no scores.

* With the sample loaded, Palmetto Pay, Atlantic Wealth Partners and Magnolia Regional Bank are flagged as outside Tampa Bay and none appears in the invite list.

* With a room size of 1, the invite list is empty and the app names the first Invite account as unable to fit.

* A budget of 40000 with 0 invited executives shows "n/a".

* Releasing a slider after one drag adds exactly one decision log entry.

* Loading the sample after changing a weight asks for confirmation, then resets weights, room size, budget and the log.

* With the sample loaded, the "Sample data, illustrative only" banner is visible.

## Constraints

* Stack: React with TypeScript, built with Vite. Plain CSS, no UI framework.

* CSV parsing may use PapaParse. No other runtime dependencies without a clear need.

* Runs entirely in the browser. All state is held in memory.

* Must work offline after install. No network calls at runtime.

* Sample data lives at public/sample/tampa_target_accounts.csv and uses only titles, never individual names.

* Scoring logic lives in a single pure function with unit tests covering requirements 4 to 7.

* Must run with npm install and npm run dev, with no environment variables or keys.
