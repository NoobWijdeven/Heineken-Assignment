# Account Compass — HEINEKEN × AISO Identify

A reproducible account-risk pipeline and Streamlit dashboard for Part 1 of the student challenge. The eight supplied files were analysed; aggregate results are in [docs/results](docs/results). The underlying data is adapted marketplace data, **not HEINEKEN customer data**.

The selected model forecasts **no placed order in the next 60 days**. It does not identify permanent churn or estimate the benefit of an intervention.

## Start the interface immediately

Use **Python 3.12**. Clone this repository and check out the implementation branch:

```bash
git clone https://github.com/NoobWijdeven/Heineken-Assignment.git
cd Heineken-Assignment
git checkout demian/identify-model
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

Without real outputs, the app loads 12 **clearly marked fictional demo accounts**. It includes search, risk/state/confidence/value/order/activity filters, sortable account tables, account details, monthly order/value/category charts, cadence charts, explanations and CSV/JSON downloads. The fictional probabilities are placeholders and have no validation metrics.

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

1. Keep `main` stable and review `demian/identify-model` through its pull request.
2. Create `teammate/action-layer` from this implementation branch (or `main` after merge).
3. Develop against `examples/scored_accounts.csv` and the selected-account JSON export.
4. Implement `recommended_action(account)` in [app/action_layer.py](app/action_layer.py).
5. Use `teammate/demo-integration` for final integration. Avoid concurrent changes to the same module; preserve schema version `1.0`.
6. For real analysis, each teammate needs the dataset separately. Raw CSVs and full account-level outputs are intentionally ignored by Git in this public repository.

Part 2 priority and Part 3 actions are extension points. They are not implemented here as final business decisions.

## Outputs

The pipeline creates `data_audit.md`, `account_features.csv`, `churn_definition_comparison.csv`, `target_sensitivity_metrics.csv`, `backtest_results.csv`, `model_metrics.csv`, `feature_importance.csv`, `feature_summary.csv`, `scored_accounts.csv`, `account_history.csv`, `account_gaps.csv`, `calibration.csv`, `risk_deciles.csv`, `risk_tier_validation.csv`, `segment_metrics.csv`, `current_activity_metrics.csv`, `backtest_predictions.csv`, `model_metadata.json` and `model_summary.md`. A trained model bundle is saved to `models/identify_model.joblib`. Load only model files you trust.

Aggregate reports from the completed run are committed in `docs/results/`; no real account-level scored table or raw dataset is committed. `examples/` is reproducible via `python -m src.make_demo`.

## Tests

```bash
python -m pytest -q
```

Tests cover line/order aggregation, string IDs, cutoff boundaries, review/delivery availability, future-data invariance, censoring, all target definitions, chronological calibration purging, preprocessing isolation, nullable JSON handoff and dashboard filtering/navigation.

## Public demo hosting

This repository contains a runnable Streamlit app, **not a hosted public demo yet**. For the eventual jury link, deploy `app/streamlit_app.py` on Streamlit Community Cloud using this branch (or `main` after merge), Python 3.12 and the root `requirements.txt`. With no `outputs/` on the host it uses the fictional fixtures. The app itself has no login gate. Verify the deployed link in a signed-out session and clearly describe the synthetic demo in the video. Do not upload raw challenge files to a public deployment by default.

## Project map

```text
src/        modular audit, features, labels, training, backtests, explanations, scoring
app/        Streamlit surface and Act extension point
examples/   fictional accounts and histories for immediate collaboration
tests/      data/model and headless Streamlit checks
docs/       methodology, handoff, measured aggregate results
data/       supplied CSVs, ignored
outputs/    generated real results, ignored
models/     generated model files, ignored
COWORK.md   original project brief, preserved verbatim
```
