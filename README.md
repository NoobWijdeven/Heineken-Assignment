# Account Compass — HEINEKEN × AISO Identify, Prioritise & Act

## Identify → Prioritise → Act (Ritmo)

The app opens on **Act: this week**: Sep's weekly visit routes, Daniel's morning audio briefing, individual account briefings, an interactive call role-play, WhatsApp drafts and a feedback dashboard. It runs on derived challenge outputs in `demo_data/`, so it can start without the eight raw CSVs. Sidebar filters apply to both Act and the account workspace.

Account Compass's 60-day Identify model has reproducible validation in this repository. Ritmo's separate 60-day risk estimates, saveability weights and rankings were generated outside it; their modelling scripts and validation reports are still needed before treating them as verified results. Call outcomes, offers, WhatsApp sending and feedback distributions are demo simulations. The optional ElevenLabs widget requires a separately configured agent; its calls are not connected to the local role-play log or route planner.

All Act screens now use the loaded Identify payload for the displayed forecast, ordering-day cadence, inactivity and account reasons. Missing Identify probabilities stay missing. Original Ritmo estimates are retained in the planning-input expander; rankings, lanes and routes remain supplied prototype proposals and are not recomputed from Identify. The account watchlist initially puts recently active accounts first; already inactive accounts remain available for reactivation review.

Outreach distinguishes a cadence check, reactivation, activity within the usual gap and insufficient cadence history. A historical service note is a question to verify, not a confirmed current complaint. Marketplace category codes have consistent neutral portfolio aliases in offers and briefings; the source codes remain available in account details. These aliases do not claim a mapping to actual HEINEKEN products. Illustrative discounts/delivery terms require approval; interest in a demo offer does not book an order. Closed/seasonal and no-current-need responses do not play or propose a discount. Changing the role-play reason resets its offer response.

- How customers are flagged and ranked, with real examples: [docs/part1_part2.md](docs/part1_part2.md)
- Act code: `app/act_engine.py` (offers, briefings, call script, WhatsApp text), `app/act_views.py` (screens), `app/action_layer.py` (`recommended_action`)
- Optional live voice agent: set `ELEVENLABS_AGENT_ID` as a Streamlit secret to show an ElevenLabs agent on the AI call screen.

A reproducible account-risk pipeline and Streamlit dashboard for Part 1 of the student challenge. The eight supplied files were analysed; aggregate results are in [docs/results](docs/results). The underlying data is adapted marketplace data, **not HEINEKEN customer data**.

The selected model forecasts **no placed order in the next 60 days**. It does not identify permanent churn or estimate the benefit of an intervention.

## Start the interface immediately

Use **Python 3.12**. Clone this repository and use the integrated `main` branch:

```bash
git clone https://github.com/NoobWijdeven/Heineken-Assignment.git
cd Heineken-Assignment
git checkout main
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app/streamlit_app.py
```

The app first uses local `outputs/`, then the bundled challenge snapshot in `demo_data/identify/`, then the 12 **clearly marked fictional accounts** in `examples/`. It includes account filters, tables, details, behavioural charts and CSV/JSON downloads. Fictional probabilities are placeholders with no validation metrics. Fictional mode does not load challenge Act routes.

## Run the real analysis

Extract all eight supplied CSV files directly into `data/`:

```text
data/
  order_lines.csv
  orders.csv
  customers.csv
  order_items.csv
  order_payments.csv
  order_reviews.csv
  products.csv
  geolocation.csv
```

```bash
python -m src.score_accounts
python -m streamlit run app/streamlit_app.py
```

The full pipeline was run on the provided 90,961 orders and 14,989 accounts. It audits keys/missingness/dates, builds cutoff-specific account features, compares four targets, evaluates five models, selects on development dates, evaluates a final held-out date, calibrates on chronological data, and scores as of **2018-08-31**. The app automatically switches to `outputs/` after a successful run.

Custom folders are supported:

```bash
python -m src.score_accounts --data-dir /path/to/csvs --output-dir /path/to/results --model-dir /path/to/models
```

Set `IDENTIFY_OUTPUT_DIR` to the matching output folder before starting Streamlit. To force the fictional demo even when real outputs exist, set it to the absolute path of `examples/`. In PowerShell, use `$env:IDENTIFY_OUTPUT_DIR = (Resolve-Path examples).Path`; on macOS/Linux, use `export IDENTIFY_OUTPUT_DIR="$PWD/examples"`.

## Measured results and their limits

The selected method is a **fitted recency baseline**, followed by chronological sigmoid calibration. It outperformed the compared methods on development PR-AUC. Cadence and the broader feature set did not justify a more complex model under the documented selection rule.

| Held-out group, 30 June 2018 cutoff | Accounts | Future inactivity | ROC-AUC | PR-AUC | Precision among top 100 |
|---|---:|---:|---:|---:|---:|
| All eligible accounts | 2,197 | 23.4% | 0.689 | 0.487 | 80% |
| Ordered within preceding 60 days | 1,821 | 17.7% | 0.584 | 0.221 | 31% |

The overall top 100 were already inactive for at least 125 days. The result is stronger for continued inactivity than for early warning. The dashboard labels **current activity** separately, and the activity-specific metrics preserve this limitation. A risk ranking alone does not identify recoverable value or the best use of a salesperson's time.

At 31 August, 2,611 accounts meet model coverage: ≥10 orders, ≥180 days of history and ≥3 positive ordering-day gaps. All 12,378 other accounts remain visible with a blank probability and **Insufficient history**. Current modelled bands are 450 High, 907 Medium and 1,254 Low. Bands use frozen development workload percentiles; they are not permanent-churn labels.

Model probabilities are estimates. Confidence is a separate evidence heuristic, not a probability or interval. Historical value is quoted merchandise value, excluding freight; no currency or realised-revenue claim is made. Final August predictions cannot be validated with future outcomes in this dataset.

Read [the model summary](docs/results/model_summary.md), [data audit](docs/results/data_audit.md) and [technical methodology](docs/METHODOLOGY.md) before using the results in the assignment.

## Collaborate without waiting for the model

The output contract is documented in [docs/HANDOFF.md](docs/HANDOFF.md). Fictional records in `examples/scored_accounts.csv` have the same 75-column schema as real outputs.

1. Pull the integrated `main` branch and create a separate branch for new changes.
2. Use the bundled challenge snapshot for the full demo, or `examples/` for isolated Identify development.
3. Extend `recommended_action(account)` in [app/action_layer.py](app/action_layer.py), preserving schema version `1.0` and nullable fields.
4. Coordinate edits to shared Streamlit modules through a pull request.
5. To rerun Identify, obtain the eight assignment CSVs separately. Raw CSVs and local generated outputs remain ignored by Git; derived demo snapshots are committed under `demo_data/`.

Part 2 uses static Ritmo exports; Part 3 demonstrates proposed actions. Neither estimates causal intervention benefit. Regenerating Identify does not regenerate Ritmo. Set `ACT_DATA_DIR` before starting the app to use another compatible Act export directory; the current contract is tied to 2018-08-31 and matching account IDs. Fictional or different-date Identify snapshots are not paired with these exports.

## Outputs

The pipeline creates `data_audit.md`, `account_features.csv`, `churn_definition_comparison.csv`, `target_sensitivity_metrics.csv`, `backtest_results.csv`, `model_metrics.csv`, `feature_importance.csv`, `feature_summary.csv`, `scored_accounts.csv`, `account_history.csv`, `account_gaps.csv`, `calibration.csv`, `risk_deciles.csv`, `risk_tier_validation.csv`, `segment_metrics.csv`, `current_activity_metrics.csv`, `backtest_predictions.csv`, `model_metadata.json` and `model_summary.md`. A trained model bundle is saved to `models/identify_model.joblib`. Load only model files you trust.

Aggregate Identify reports are in `docs/results/`. Derived account-level challenge outputs are committed in `demo_data/identify/`, and Ritmo priority/route exports are in `demo_data/ritmo/`. Raw datasets are excluded. `examples/` is reproducible via `python -m src.make_demo`. Original Identify reports describe the analysis before the Act integration.

## Tests

```bash
python -m pytest -q
```

Tests cover the Identify pipeline and UI, sparse-account Act handling, separation of fictional/challenge snapshots, morning briefings, route navigation, filters and call-role-play outcomes. Recorded-demo regression cases check conflicting forecasts/cadence, dormant versus recently active accounts, portfolio offers, spoken branch text and stale acceptance state. Browser speech playback and the optional external ElevenLabs agent need separate manual verification.

## Public demo hosting

For the jury link, deploy `app/streamlit_app.py` from `main`, using Python 3.12 and the root `requirements.txt`. With no `outputs/` on the host, it uses the bundled challenge snapshot. The app has no login gate. Verify the deployed link in a signed-out session and describe which actions and feedback are simulated in the video. Hosting, the 3-minute video and the 1-page summary remain submission tasks.

## Project map

```text
src/        modular audit, features, labels, training, backtests, explanations, scoring
app/        Streamlit surface, Act logic and spoken briefings
demo_data/  derived challenge Identify snapshot and external Ritmo exports
examples/   fictional accounts and histories for immediate collaboration
tests/      data/model and headless Streamlit checks
docs/       methodology, handoff, measured aggregate results
data/       supplied CSVs, ignored
outputs/    generated real results, ignored
models/     generated model files, ignored
COWORK.md   original project brief, preserved verbatim
```
