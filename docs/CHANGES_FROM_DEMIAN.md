# What changed compared to Demian's version

This is a short handoff for Demian. It lists everything that changed on branch `teammate/action-layer` (PR #2) compared to his branch `demian/identify-model`. Nothing in his pipeline (`src/`) or tests was changed.

## In one sentence

Account Compass now also does Part 2 (who to help first) and Part 3 (what to do), on top of his Part 1 risk score.

## What stays exactly the same

- The pipeline in `src/`: features, models, backtests, the recency model and its 60-day forecast.
- The tests in `tests/`.
- The data contract: `scored_accounts.csv` columns, `selected_account_payload()`, schema version 1.0.
- The "Account workspace" and "Validation & handoff" tabs work as before.

## What is new

| What | Where | Plain explanation |
| --- | --- | --- |
| New first tab **"Act: this week"** | `app/act_views.py` | Four screens: **Rep's week** (map of 12 visits per week with a "why card" and a read-aloud briefing per shop), **AI call** (a call agent that says what changed, asks *why*, and books an offer or hands the shop to the rep), **WhatsApp** (ready messages in Portuguese for small shops) and **What we learn** (chart of the reasons customers give). |
| The Act hook is filled in | `app/action_layer.py` | `recommended_action(account)` now returns the lane (rep visit, AI call, WhatsApp or monitor), the priority rank, the reasons and the offer, instead of the placeholder text. It still returns `title` and `message`, so the contract holds. |
| Offer, briefing and script logic | `app/act_engine.py` | Builds the offer (the dropped product bundled with the shop's usual order, or a restock reminder), the 30-second briefing, the call script and the WhatsApp text. It only reads files; nothing is re-scored. |
| Prioritisation data (Part 2) | `demo_data/ritmo/` | `priority_list.csv` (rank, lane, chance, reasons for every account) and `lane_a_routes.csv` (weekly rep routes). Made by the Ritmo scripts, outside this repo. |
| His real pipeline results | `demo_data/identify/` | A copy of his `outputs/` from a full run on the challenge data, so the hosted app shows real numbers instead of the 12 fictional demo accounts. |
| Explanation of Parts 1 and 2 | `docs/part1_part2.md` | Churn definition, warning signs, priority formula, lanes and real example accounts. |

## Small edits to his files

- `app/streamlit_app.py`
  - Adds the new tab and uses the richer action card in the Account workspace.
  - If `outputs/` is missing, it now loads `demo_data/identify/` before falling back to `examples/`. Running his pipeline still takes priority.
  - Title and hero text now say "Identify · Prioritise · Act".
- `README.md`: a short section at the top about the Act tab, with links.

## How his score and Ritmo fit together

- **His score** says *how likely* a shop is to stop ordering. It covers the 2,611 accounts with 10+ orders and is shown on every card as "Account Compass 60-day forecast".
- **Ritmo** adds *who to help first*: money spent last year × chance of going silent for 60 days × chance it can still be won back. It also adds the plain-word reasons and the lane, for all 9,735 accounts with 3+ orders.

## Churn is now 60 days everywhere

Zep decided that churn means **60 days without an order**, the same window as Demian's score. The Ritmo scripts were rerun with 60 days, and `demo_data/ritmo/` holds the new files. The app and `docs/part1_part2.md` now say 60 days throughout.

What moved with the switch:
- Niterói (the demo shop) is now **#17**, with a 24% chance of leaving. It's still on the Rio week 1 route.
- Lanes: 150 rep visits, 850 AI calls, 7,016 WhatsApp messages, 6,973 to monitor.
- Rep routes: São Paulo 43 visits, Minas Gerais 21, Rio de Janeiro 16, plus smaller states.
- Dropping a core product is now 2 to 2.6x the risk (it was 3.5x with 90 days).

## Known test result

17 of 18 tests pass. `test_future_purchases_cannot_change_features` fails on a pandas 3 string-type difference, because the test machine had pandas 3 instead of the pinned 2.2.3. It is not caused by these changes.
