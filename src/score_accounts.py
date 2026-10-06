"""Run audit, feature engineering, target comparison, temporal validation and scoring."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits
from .config import (DATA_DIR, OUTPUT_DIR, MODEL_DIR, ANALYSIS_DATE, MODEL_VERSION,
                     SNAPSHOT_DATES, TARGET, HORIZON_DAYS, TEST_CUTOFF, SEED)
from .load_data import load_data
from .clean_data import audit_data
from .build_features import build_features, account_history
from .churn_labels import build_labels, compare_definitions
from .backtest import run_backtests
from .train_model import train_model, temporal_training_split
from .evaluate import risk_tiers
from .explain import explanation_records
from .target_sensitivity import target_sensitivity


def run(data_dir=DATA_DIR, output_dir=OUTPUT_DIR, model_dir=MODEL_DIR):
    for folder in [output_dir, model_dir]:
        folder.mkdir(parents=True, exist_ok=True)
    print("Loading and auditing the eight source files", flush=True)
    data = load_data(data_dir)
    audit_data(data, output_dir)
    snapshots, labelled = {}, []
    for date in SNAPSHOT_DATES:
        f = build_features(data, date)
        snapshots[date] = f
        e = f[f.model_eligible]
        if len(e):
            labels = build_labels(data, e, TARGET)
            labelled.append(e.merge(labels, on="account_id").dropna(subset=["label"]))
        print(f"Snapshot {date}: {len(f):,} accounts, {len(e):,} eligible", flush=True)
    target_comparison = compare_definitions(data, snapshots)
    target_comparison.to_csv(output_dir / "churn_definition_comparison.csv", index=False)
    labelled = pd.concat(labelled, ignore_index=True)
    print("Walk-forward comparison and held-out evaluation", flush=True)
    with threadpool_limits(limits=2):
        target_sensitivity(data, snapshots).to_csv(output_dir / "target_sensitivity_metrics.csv", index=False)
        results = run_backtests(labelled)
        fit, cal = temporal_training_split(labelled, ANALYSIS_DATE)
        final_model = train_model(results["selected_model"], fit, cal)
        f = build_features(data, ANALYSIS_DATE)
        f.to_csv(output_dir / "account_features.csv", index=False)
        scored = f.copy()
        scored["risk_probability"] = np.nan
        scored.loc[scored.model_eligible, "risk_probability"] = final_model.predict(scored[scored.model_eligible])
        scored["risk_score"] = (scored.risk_probability * 100).round(1)
        scored["risk_level"] = "Insufficient history"
        scored.loc[scored.model_eligible, "risk_level"] = risk_tiers(scored.loc[scored.model_eligible, "risk_probability"], results["thresholds"])
        explanations = explanation_records(scored, final_model, fit[final_model.features].median())
    scored = scored.merge(explanations, on="account_id", validate="one_to_one")
    scored["model_version"] = MODEL_VERSION
    scored["model_name"] = final_model.name
    scored["target_definition"] = TARGET
    scored["prediction_horizon_days"] = HORIZON_DAYS
    scored["prediction_status"] = np.where(scored.model_eligible, "modelled", "insufficient_history")
    scored["data_kind"] = "challenge"
    scored["schema_version"] = "1.0"
    scored["current_activity"] = np.where(scored.days_since_last_order > 60, "Inactive over 60 days", "Ordered within 60 days")
    scored.to_csv(output_dir / "scored_accounts.csv", index=False)
    account_history(data, ANALYSIS_DATE).to_csv(output_dir / "account_history.csv", index=False)
    # Every distinct order day is sufficient for cadence plotting; no buyer/review text exported.
    days = data.orders[data.orders.order_day <= pd.Timestamp(ANALYSIS_DATE)][["account_id", "order_day"]].drop_duplicates().copy()
    days = days.sort_values(["account_id", "order_day"])
    days["gap_days"] = days.groupby("account_id").order_day.diff().dt.days
    days.to_csv(output_dir / "account_gaps.csv", index=False)
    results["metrics"].to_csv(output_dir / "model_metrics.csv", index=False)
    results["metrics"].to_csv(output_dir / "backtest_results.csv", index=False)
    for key, filename in [("importance", "feature_importance"), ("reliability", "calibration"), ("deciles", "risk_deciles"),
                          ("tier_metrics", "risk_tier_validation"), ("segment_metrics", "segment_metrics"), ("activity_metrics", "current_activity_metrics"), ("predictions", "backtest_predictions")]:
        results[key].to_csv(output_dir / f"{filename}.csv", index=False)
    feature_summary = f.select_dtypes(include="number").describe().transpose()
    feature_summary.to_csv(output_dir / "feature_summary.csv")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data_dir.glob("*.csv"))}
    holdout = results["metrics"][results["metrics"].split == "holdout"].iloc[0].to_dict()
    warning = ""
    if holdout["top_decile_lift"] < 1.2 or holdout["roc_auc"] < .6:
        warning = "Predictive separation is weak on the held-out cutoff; treat risk estimates as exploratory."
    if holdout["calibration_ece"] > .1:
        warning += " Probability calibration differs materially from observed outcomes."
    active_metrics = results["activity_metrics"][results["activity_metrics"].current_activity == "Ordered within last 60 days"].iloc[0].to_dict()
    warning = (warning + " Overall top-risk accuracy includes already inactive accounts. Early-warning estimates for recently active accounts are exploratory.").strip()
    metadata = {"model_version": MODEL_VERSION, "schema_version": "1.0", "analysis_date": ANALYSIS_DATE,
                "selected_model": final_model.name, "best_dev_pr_auc_model": results["best_pr_auc_model"],
                "target_definition": TARGET, "prediction_horizon_days": HORIZON_DAYS,
                "thresholds": results["thresholds"], "random_seed": SEED, "holdout": holdout, "holdout_cutoff": TEST_CUTOFF, "active_account_holdout": active_metrics,
                "validation_warning": warning.strip(), "data_kind": "challenge", "source_sha256": hashes,
                "runtime": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__},
                "training_manifest": results["manifests"],
                "production_training": {"fit_cutoffs": final_model.fit_cutoffs, "calibration_cutoff": final_model.calibration_cutoff,
                                        "fit_max_label_end": str(fit.label_end_date.max()), "calibration_max_label_end": str(cal.label_end_date.max()),
                                        "fit_rows": len(fit), "calibration_rows": len(cal),
                                        "calibration_mode": "sigmoid" if final_model.calibration is not None else "prevalence fallback"}}
    (output_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2, default=str) + "\n")
    joblib.dump({"model": final_model, "metadata": metadata}, model_dir / "identify_model.joblib")
    write_summary(results, target_comparison, scored, metadata, output_dir)
    print(f"Selected: {final_model.name}; scored {scored.model_eligible.sum():,}/{len(scored):,} accounts", flush=True)
    print(f"Held-out ROC-AUC {holdout['roc_auc']:.3f}; PR-AUC {holdout['pr_auc']:.3f}; top-100 precision {holdout['precision_at_100']:.0%}", flush=True)
    return metadata


def write_summary(results, comparison, scored, metadata, output_dir):
    h = metadata["holdout"]
    active = metadata["active_account_holdout"]
    summary = ["# Identify model summary", "", "## Target and population", "",
               "The prediction is the probability of **no placed order in the next 60 days**, not confirmed permanent churn. Scoring date: 31 August 2018.",
               "The main population has at least 10 orders, at least 180 days of observed history, and at least three positive gaps between distinct order days.",
               f"At the scoring date, {scored.model_eligible.sum():,} of {len(scored):,} accounts qualify; the remainder are retained with nullable probability and 'Insufficient history'.", "",
               "## Why 60 days", "",
               "Target selection uses February/April development evidence. At those dates, 95th-percentile typical reorder gaps are below 60 days and very few established accounts normally exceed 60 days. May labels are reported only as retrospective sensitivity and do not select the target. Sixty days is an early-warning horizon with more positive examples than 90 days, without waiting three months to evaluate an intervention.",
               "This is a documented business choice informed by cadence and label prevalence, not a definition selected to maximise accuracy. Cadence-adjusted labels have variable action windows; the frequency-decline label excludes accounts without a sufficient recent baseline. Both remain alternatives for later sensitivity work.", "",
               "| Cutoff | Candidate | Labelled | Positive rate |", "|---|---|---:|---:|"]
    summary += [f"| {r.cutoff} | {r.definition} | {r.labelled_accounts:,} | {r.positive_rate:.1%} |" for r in comparison.itertuples()]
    summary += ["", "## Validation and selected model", "",
                f"Selected method: **{metadata['selected_model']}**. Models compared: fitted recency baseline, fitted cadence baseline, logistic regression, random forest and gradient boosting.",
                "Development cutoffs are 28 February and 30 April 2018. Model selection uses mean PR-AUC and a documented simplicity preference (within 0.01 PR-AUC, 0.02 top-100 precision and 0.01 Brier of the strongest candidate). The selected method and tier thresholds are frozen before the 30 June 2018 holdout.",
                "Every training target matures before the decision date. Calibration uses the most recent matured snapshot; fit-target windows end before that calibration snapshot. Calibration is sigmoid on disjoint chronological rows, with a prevalence fallback if its slope is non-positive.",
                "Evaluation windows are March–April, May–June, and July–August. They do not overlap. The same accounts can recur across snapshots: this tests future predictions for existing accounts, not performance on unseen accounts.",
                f"Held-out prevalence: {h['prevalence']:.1%}; ROC-AUC: {h['roc_auc']:.3f}; PR-AUC: {h['pr_auc']:.3f}; precision@100: {h['precision_at_100']:.1%}; top-decile lift: {h['top_decile_lift']:.2f}×.",
                f"Held-out Brier: {h['brier']:.3f}; prevalence-only reference: {h['brier_prevalence_baseline']:.3f}; calibration ECE: {h['calibration_ece']:.3f}.",
                "Tier thresholds are development 75th/90th probability percentiles, representing historical workload bands; they are not universal definitions of high risk. Binary classification uses a development F1 threshold. All tier precision and calibration tables are exported.", "",
                "## Current inactivity versus early warning", "",
                f"For accounts ordered within the previous 60 days, held-out ROC-AUC is {active['roc_auc']:.3f}, PR-AUC {active['pr_auc']:.3f}, and precision@100 {active['precision_at_100']:.1%} against prevalence {active['prevalence']:.1%}. This subgroup performance is exploratory, not a separate validated model.",
                "Overall top-risk performance is substantially influenced by already dormant accounts. The dashboard labels current inactivity separately. Risk ranking alone does not estimate recoverability, account priority or the benefit of contacting an account. Historical value, not recent spend alone, is used for value-coverage diagnostics; no revenue-at-risk claim is made.", "",
                "## Predictive signals", "",
                "Held-out permutation importance is measured as the change in PR-AUC when one feature is shuffled, after model selection. Correlated inputs can share or mask importance. No causal conclusions are supported.",
                "| Input | PR-AUC change | Standard deviation |", "|---|---:|---:|"]
    summary += [f"| {r.feature} | {r.importance_pr_auc:.4f} | {r.importance_std:.4f} |" for r in results['importance'].head(10).itertuples()]
    summary += ["", "## Evidence and handoff", "",
                "Account explanations distinguish model sensitivity (one input replaced with its fit-sample median) from observed context such as review or delivery events. This sensitivity is not additive or causal; correlated input replacements may be unrealistic. Supporting observations are never claimed to have driven the model.",
                "Confidence is an evidence heuristic, not a calibrated probability or interval. Low means outside the validated population; High requires 20+ orders, 365+ days and gap coefficient of variation ≤1; other eligible accounts are Medium. An auxiliary evidence score combines order count, age, gap count and review/delivery coverage with documented illustrative weights.",
                "The Act layer reads scored_accounts.csv as text account IDs, uses only modelled probabilities, and receives selected-account JSON from the dashboard. Risk, relative account value and confidence stay separate. No recoverability or causal intervention benefit is estimated.", "",
                "## Leakage checks", "",
                "- Purchases are filtered to the full cutoff day before aggregation.",
                "- Joined review scores are ignored; original response timestamps gate review availability.",
                "- Deliveries are included only after their original delivery event occurs.",
                "- Final order status is excluded because historical status transition times are unavailable.",
                "- Prices/categories are assumed to be purchase-time attributes; immutable history is not independently available.",
                "- Outcomes occur after each cutoff; right-censored labels are nullable and excluded.",
                "- Imputation/scaling fit on training rows only; fit labels mature before calibration features.",
                "- Calibration outcomes mature by the decision date; held-out outcomes never select the model or thresholds.",
                "- Unique order keys drive counts; item prices are summed once per distinct line.", "",
                "## Limitations and next steps", "",
                "This is anonymised marketplace data grouped by ZIP area, not observed HEINEKEN commercial accounts. Placed orders and merchandise value are proxies, not fulfilled sales and revenue. Dataset growth adjustment is descriptive and is not a causal control. The horizon is short; repeated accounts, changing prevalence and only one final holdout limit generalisation. Sparse accounts are not modelled. Historical labels are simulated future inactivity, not known lost relationships.",
                "Probability calibration and workload bands may drift by August. No outcomes after 31 August are available to validate final scores. Confirmation of historical order-status availability, additional time periods, intervention data and validation in actual commercial accounts are needed before operational use.",
                "Review text and buyer identifiers are excluded from exports and UI. Raw CSVs, full real outputs and model binaries are ignored by Git; the repository contains a clearly marked synthetic demo and aggregate measured results."]
    if metadata['validation_warning']:
        summary += ["", f"**Validation limitation:** {metadata['validation_warning']}"]
    (output_dir / "model_summary.md").write_text("\n".join(summary) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir, args.model_dir)


if __name__ == "__main__":
    main()
