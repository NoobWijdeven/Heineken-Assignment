# Technical methodology

## Time, identity and order/value accounting

An account is the supplied text `account_id`, representing a ZIP area. This account construction is part of the adapted challenge and does not establish a real customer relationship. The canonical order table has one row per order. Product lines are checked for duplicate `(order_id, order_item_id)` keys; their merchandise prices are summed once per order, excluding freight. Denormalised account maps and purchase dates must agree with original orders.

An analysis date includes its entire calendar day. Purchases before the following midnight are included. Order categories and quoted prices are assumed available at purchase; price/category revision histories are unavailable. Eventual order status is not a feature, a label filter, or a basis for excluding accounts, because status-transition timestamps are unavailable. Consequently the target is about **placed orders**, not successful fulfilment.

The final snapshot is 31 August 2018. Future events present in the files do not expand the observation horizon. Original review response timestamps, together with creation timestamps, gate review availability. A questionnaire's creation does not make its future score known. Original customer delivery timestamps gate service outcomes; joined final review scores, late flags and delivery dates are not used directly.

## Features

Features are generated independently at each cutoff:

- Order history, tenure, active months and recency use distinct orders.
- Cadence uses distinct purchase **days**, avoiding artificial zero-day gaps from multiple same-day purchases. Gap count, median, mean, standard deviation, variation, last completed gap and historical p90 are available.
- Trailing 30/60/90-day order/value windows include the cutoff day; the preceding 90-day window ends exactly 90 days before it. Changes are nullable when the denominator is zero or a full 180-day history is unavailable.
- Dataset-adjusted order/value change divides each account's window ratio by the overall dataset ratio, calculated only at that cutoff. This is descriptive adjustment for growth, not a causal control or seasonality model.
- Category counts are distinct categories. A repeated category has ≥2 distinct orders in the preceding 90 days; absence in the recent 90 days produces a descriptive dropout flag. This operational definition is not independently validated as a causal churn signal. Product category names stand for portfolio lines.
- Delivery rates average **known delivered orders**, not item lines. Early deliveries contribute zero to positive-delay averages. Recent service windows use the delivery event date. No known deliveries means a missing rate, not a zero rate.
- Review averages use one latest available review per order; trends compare response-event windows. Missing reviews remain unknown.

Location and account IDs are interface fields, not predictive inputs. Buyer identifiers, review text, payment methods, product dimensions and coordinates are not exported as model inputs.

## Population and target selection

The model covers accounts with ≥10 placed orders, ≥180 days of observation and ≥3 positive order-day gaps. Accounts outside coverage are retained with null risk estimates; low-order segments are not silently removed. Broad counts for 1, 2–4, 5–9 and 10+ order segments appear in the audit. Held-out metrics subdivide modelled accounts into 10–19, 20–49 and 50+ orders.

Four targets are implemented:

| Target | Outcome | Eligibility beyond model coverage |
|---|---|---|
| `inactivity_60d` | Zero placed orders in `(T, T+60 days]` | Full 60-day follow-up |
| `inactivity_90d` | Zero placed orders in `(T, T+90 days]` | Full 90-day follow-up |
| `frequency_decline_60d` | Next-60-day order count below 50% of past-60-day count | ≥2 orders in past 60 days; full follow-up |
| `cadence_inactivity` | Zero orders over `ceil(2 × median historical gap)`, capped to 30–90 days | Known cadence; full account-specific follow-up |

Labels beyond 31 August are censored and remain nullable. These are operational forecast outcomes, not confirmed lost relationships. Target counts/prevalence are compared at February, April and May snapshots. February/April development evidence informs the 60-day choice; May is retrospective sensitivity only, and does not select the target. Separate development model comparisons for all four targets are in `target_sensitivity_metrics.csv`.

Sixty days exceeds the p95 of typical gaps in the development population, has more positives than 90 days, and offers a consistent intervention horizon. This business choice is documented rather than selecting the label with the best model accuracy. Cadence-relative and frequency-decline labels remain alternatives for future analysis.

## Temporal model comparison

Snapshots are monthly from May 2017 to June 2018; early snapshots without mature eligible accounts are not used for fitting. Each simulated decision can access only matured historical labels. The most recent matured snapshot is reserved for probability calibration. Model-fitting label windows must end on or before that calibration snapshot's feature cutoff. This purges forward outcome overlap between fit and calibration.

| Phase | Decision cutoff | Future-outcome window | Role |
|---|---|---|---|
| Development 1 | 2018-02-28 | 2018-03-01 to 2018-04-29 | Model comparison |
| Development 2 | 2018-04-30 | 2018-05-01 to 2018-06-29 | Model comparison / thresholds |
| Final holdout | 2018-06-30 | 2018-07-01 to 2018-08-29 | Frozen-method evaluation |
| Final scoring | 2018-08-31 | Not observed | No final labels available |

The three evaluation outcome windows do not overlap. The same account may recur across snapshots, as the use case is repeated scoring of existing accounts. This does not measure generalisation to entirely new account identities. Training windows can overlap each other, and repeated account observations are dependent; no independent-sample confidence interval is claimed. Monthly changing account eligibility and dataset volume can affect observed prevalence.

Preprocessing is median imputation with missingness indicators and standard scaling, fitted only on model-training rows. Models use fixed configurations and seed 42:

- Recency baseline: logistic regression on inactive days.
- Cadence baseline: logistic regression on cadence ratio.
- Full logistic regression on 34 behavioural/evidence features.
- Random forest: 150 trees, maximum depth 6, minimum leaf 20.
- Histogram gradient boosting: 100 iterations, at most 7 leaves, minimum leaf 25, L2 penalty 3.

No random train/test split is used. Probabilities are transformed by a sigmoid fitted on the separate chronological calibration snapshot. If its slope is non-positive, the implementation records a prevalence-only calibration fallback. Missingness is not replaced with favourable service values.

Select the strongest mean development PR-AUC, then prefer the earliest simpler model within 0.01 PR-AUC, 0.02 precision@100 and 0.01 Brier of that candidate. Thresholds are frozen before final holdout: development 75th/90th probability percentiles for workload bands, and the best development F1 threshold for binary diagnostics. Their use does not imply universally correct churn categories.

After evaluation, the chosen method is fitted on the later matured history available for August, with a newly chronological calibration snapshot. Model type and tier thresholds remain frozen. Data hashes, cutoffs, fit/calibration counts, runtime versions and seed are recorded in the run manifest. Reproduction uses the pinned dependencies and original eight files.

## Metrics, evidence and limits

Exports include ROC-AUC, PR-AUC (average precision), precision/recall/F1, confusion counts, Brier score, binned calibration/ECE, precision@100, value coverage and decile lift. Value coverage uses historical quoted merchandise value; it is not recoverable value, revenue at risk or intervention benefit. Calibration-bin estimates can be noisy.

The selected recency baseline has higher overall top-100 precision than it does among recently active accounts. The latter subgroup is explicitly reported because early warning is commercially different from continued dormancy. The interface separates `current_activity` from predicted `risk_level`.

Permutation importance is diagnostic after selection: shuffle one input and measure held-out PR-AUC change. Local explanations replace one input with its fit median and report the probability difference. These replacements are not additive feature attributions; correlated replacements may be implausible. Supporting service/category/review observations are labelled separately and are not asserted to drive the selected model.

Evidence confidence is heuristic. Low means outside model coverage. High means ≥20 orders, ≥365 days and gap coefficient of variation ≤1. Other eligible accounts are Medium. The auxiliary evidence score uses clipped order count/30 (40%), age/365 (25%), gaps/15 (20%) and mean review/delivery coverage (15%). These weights are illustrative and are not learned or empirically calibrated confidence estimates. No risk score uses these confidence weights.

Short observation history, constructed ZIP accounts, weak early-warning separation, changing prevalence and the absence of actual customer-loss/intervention labels limit operational conclusions. Review/service associations and feature importance do not support causal statements. The final August scores have no observable future labels. Additional periods, real account identities and prospective validation are needed for operational deployment.

## Checks

The test suite exercises string IDs, item/order accounting, timestamp cutoffs, exclusion of unavailable review/delivery outcomes, invariance to future purchases, unknown evidence, right censoring, all target paths, purged calibration chronology, training-only preprocessing, synthetic schema/JSON compatibility and dashboard search/navigation/filtering. The full pipeline and both real and synthetic dashboard modes were executed locally.

References: [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html) and [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing). The original assignment brief is preserved in `COWORK.md`.
