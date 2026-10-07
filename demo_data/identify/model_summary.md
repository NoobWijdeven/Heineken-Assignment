# Identify model summary

## Target and population

The prediction is the probability of **no placed order in the next 60 days**, not confirmed permanent churn. Scoring date: 31 August 2018.
The main population has at least 10 orders, at least 180 days of observed history, and at least three positive gaps between distinct order days.
At the scoring date, 2,611 of 14,989 accounts qualify; the remainder are retained with nullable probability and 'Insufficient history'.

## Why 60 days

Target selection uses February/April development evidence. At those dates, 95th-percentile typical reorder gaps are below 60 days and very few established accounts normally exceed 60 days. May labels are reported only as retrospective sensitivity and do not select the target. Sixty days is an early-warning horizon with more positive examples than 90 days, without waiting three months to evaluate an intervention.
This is a documented business choice informed by cadence and label prevalence, not a definition selected to maximise accuracy. Cadence-adjusted labels have variable action windows; the frequency-decline label excludes accounts without a sufficient recent baseline. Both remain alternatives for later sensitivity work.

| Cutoff | Candidate | Labelled | Positive rate |
|---|---|---:|---:|
| 2018-02-28 | inactivity_60d | 1,256 | 16.5% |
| 2018-02-28 | inactivity_90d | 1,256 | 11.4% |
| 2018-02-28 | frequency_decline_60d | 1,001 | 30.1% |
| 2018-02-28 | cadence_inactivity | 1,256 | 24.4% |
| 2018-04-30 | inactivity_60d | 1,746 | 21.6% |
| 2018-04-30 | inactivity_90d | 1,746 | 15.0% |
| 2018-04-30 | frequency_decline_60d | 1,223 | 31.5% |
| 2018-04-30 | cadence_inactivity | 1,746 | 29.7% |
| 2018-05-31 | inactivity_60d | 1,983 | 24.4% |
| 2018-05-31 | inactivity_90d | 1,983 | 14.8% |
| 2018-05-31 | frequency_decline_60d | 1,312 | 33.0% |
| 2018-05-31 | cadence_inactivity | 1,983 | 33.4% |

## Validation and selected model

Selected method: **recency_baseline**. Models compared: fitted recency baseline, fitted cadence baseline, logistic regression, random forest and gradient boosting.
Development cutoffs are 28 February and 30 April 2018. Model selection uses mean PR-AUC and a documented simplicity preference (within 0.01 PR-AUC, 0.02 top-100 precision and 0.01 Brier of the strongest candidate). The selected method and tier thresholds are frozen before the 30 June 2018 holdout.
Every training target matures before the decision date. Calibration uses the most recent matured snapshot; fit-target windows end before that calibration snapshot. Calibration is sigmoid on disjoint chronological rows, with a prevalence fallback if its slope is non-positive.
Evaluation windows are March–April, May–June, and July–August. They do not overlap. The same accounts can recur across snapshots: this tests future predictions for existing accounts, not performance on unseen accounts.
Held-out prevalence: 23.4%; ROC-AUC: 0.689; PR-AUC: 0.487; precision@100: 80.0%; top-decile lift: 2.70×.
Held-out Brier: 0.157; prevalence-only reference: 0.179; calibration ECE: 0.034.
Tier thresholds are development 75th/90th probability percentiles, representing historical workload bands; they are not universal definitions of high risk. Binary classification uses a development F1 threshold. All tier precision and calibration tables are exported.

## Current inactivity versus early warning

For accounts ordered within the previous 60 days, held-out ROC-AUC is 0.584, PR-AUC 0.221, and precision@100 31.0% against prevalence 17.7%. This subgroup performance is exploratory, not a separate validated model.
Overall top-risk performance is substantially influenced by already dormant accounts. The dashboard labels current inactivity separately. Risk ranking alone does not estimate recoverability, account priority or the benefit of contacting an account. Historical value, not recent spend alone, is used for value-coverage diagnostics; no revenue-at-risk claim is made.

## Predictive signals

Held-out permutation importance is measured as the change in PR-AUC when one feature is shuffled, after model selection. Correlated inputs can share or mask importance. No causal conclusions are supported.
| Input | PR-AUC change | Standard deviation |
|---|---:|---:|
| days_since_last_order | 0.2523 | 0.0072 |

## Evidence and handoff

Account explanations distinguish model sensitivity (one input replaced with its fit-sample median) from observed context such as review or delivery events. This sensitivity is not additive or causal; correlated input replacements may be unrealistic. Supporting observations are never claimed to have driven the model.
Confidence is an evidence heuristic, not a calibrated probability or interval. Low means outside the validated population; High requires 20+ orders, 365+ days and gap coefficient of variation ≤1; other eligible accounts are Medium. An auxiliary evidence score combines order count, age, gap count and review/delivery coverage with documented illustrative weights.
The Act layer reads scored_accounts.csv as text account IDs, uses only modelled probabilities, and receives selected-account JSON from the dashboard. Risk, relative account value and confidence stay separate. No recoverability or causal intervention benefit is estimated.

## Leakage checks

- Purchases are filtered to the full cutoff day before aggregation.
- Joined review scores are ignored; original response timestamps gate review availability.
- Deliveries are included only after their original delivery event occurs.
- Final order status is excluded because historical status transition times are unavailable.
- Prices/categories are assumed to be purchase-time attributes; immutable history is not independently available.
- Outcomes occur after each cutoff; right-censored labels are nullable and excluded.
- Imputation/scaling fit on training rows only; fit labels mature before calibration features.
- Calibration outcomes mature by the decision date; held-out outcomes never select the model or thresholds.
- Unique order keys drive counts; item prices are summed once per distinct line.

## Limitations and next steps

This is anonymised marketplace data grouped by ZIP area, not observed HEINEKEN commercial accounts. Placed orders and merchandise value are proxies, not fulfilled sales and revenue. Dataset growth adjustment is descriptive and is not a causal control. The horizon is short; repeated accounts, changing prevalence and only one final holdout limit generalisation. Sparse accounts are not modelled. Historical labels are simulated future inactivity, not known lost relationships.
Probability calibration and workload bands may drift by August. No outcomes after 31 August are available to validate final scores. Confirmation of historical order-status availability, additional time periods, intervention data and validation in actual commercial accounts are needed before operational use.
Review text and buyer identifiers are excluded from exports and UI. Raw CSVs, full real outputs and model binaries are ignored by Git; the repository contains a clearly marked synthetic demo and aggregate measured results.

**Validation limitation:** Overall top-risk accuracy includes already inactive accounts. Early-warning estimates for recently active accounts are exploratory.
