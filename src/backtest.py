"""Walk-forward model choice on development cutoffs; one untouched final cutoff."""
import numpy as np
import pandas as pd
from .config import DEV_CUTOFFS, TEST_CUTOFF, MODELS, SEED
from .train_model import train_model, temporal_training_split
from .evaluate import evaluate, select_thresholds, reliability_table, decile_table, risk_tiers
from sklearn.inspection import permutation_importance


def run_backtests(labelled):
    metrics, predictions, manifests = [], [], []
    for date in DEV_CUTOFFS:
        test = labelled[labelled.analysis_date == date]
        fit, cal = temporal_training_split(labelled, date)
        for name in MODELS:
            model = train_model(name, fit, cal)
            p = model.predict(test)
            metrics.append({"cutoff": date, "split": "development", "model": name,
                            **evaluate(test.label, p, test.historical_spend)})
            predictions.append(pd.DataFrame({"cutoff": date, "model": name, "account_id": test.account_id,
                                             "label": test.label, "probability": p, "value_proxy": test.historical_spend,
                                             "historical_order_count": test.historical_order_count}))
            manifests.append({"decision_date": date, "model": name, "fit_snapshots": model.fit_cutoffs,
                              "calibration_snapshot": model.calibration_cutoff, "fit_rows": len(fit),
                              "calibration_rows": len(cal), "fit_max_label_end": str(fit.label_end_date.max()),
                              "calibration_max_label_end": str(cal.label_end_date.max()),
                              "calibration_mode": "sigmoid" if model.calibration is not None else "prevalence fallback"})
    dev_metrics = pd.DataFrame(metrics)
    averages = dev_metrics.groupby("model").mean(numeric_only=True)
    best = averages.pr_auc.idxmax()
    # Prefer a simpler method when development PR-AUC/top-100/Brier gains are small.
    order = ["recency_baseline", "cadence_baseline", "logistic", "random_forest", "gradient_boosting"]
    selected = best
    for name in order:
        if (averages.loc[name, "pr_auc"] >= averages.loc[best, "pr_auc"] - .01
                and averages.loc[name, "precision_at_100"] >= averages.loc[best, "precision_at_100"] - .02
                and averages.loc[name, "brier"] <= averages.loc[best, "brier"] + .01):
            selected = name
            break
    dev_predictions = pd.concat(predictions, ignore_index=True)
    thresholds = select_thresholds(dev_predictions[dev_predictions.model == selected])
    # Fixed model and thresholds before evaluating this last cutoff.
    test = labelled[labelled.analysis_date == TEST_CUTOFF]
    fit, cal = temporal_training_split(labelled, TEST_CUTOFF)
    model = train_model(selected, fit, cal)
    p = model.predict(test)
    metrics.append({"cutoff": TEST_CUTOFF, "split": "holdout", "model": selected,
                    **evaluate(test.label, p, test.historical_spend, thresholds["binary"])})
    # Re-evaluate development confusion metrics at the selected, frozen binary threshold.
    for row in metrics[:-1]:
        pred = dev_predictions[(dev_predictions.cutoff == row["cutoff"]) & (dev_predictions.model == row["model"])]
        row.update(evaluate(pred.label, pred.probability, pred.value_proxy, thresholds["binary"]))
    manifests.append({"decision_date": TEST_CUTOFF, "model": selected, "fit_snapshots": model.fit_cutoffs,
                      "calibration_snapshot": model.calibration_cutoff, "fit_rows": len(fit), "calibration_rows": len(cal),
                      "fit_max_label_end": str(fit.label_end_date.max()), "calibration_max_label_end": str(cal.label_end_date.max()),
                      "calibration_mode": "sigmoid" if model.calibration is not None else "prevalence fallback"})
    # Importance is diagnostic only, computed AFTER selection on the holdout.
    def scorer(estimator, X, y):
        from sklearn.metrics import average_precision_score
        return average_precision_score(y, model.predict(X))
    # RiskModel deliberately exposes predict as calibrated probabilities to this scorer.
    importance = permutation_importance(model.estimator, test[model.features], test.label.astype(int),
                                        scoring=scorer, n_repeats=5, random_state=SEED, n_jobs=1)
    importance_table = pd.DataFrame({"feature": model.features,
                                     "importance_pr_auc": importance.importances_mean,
                                     "importance_std": importance.importances_std}).sort_values("importance_pr_auc", ascending=False)
    holdout_predictions = pd.DataFrame({"cutoff": TEST_CUTOFF, "model": selected, "account_id": test.account_id,
                                       "label": test.label, "probability": p, "value_proxy": test.historical_spend,
                                       "historical_order_count": test.historical_order_count})
    tier_rows = []
    for split, frame in [("development", dev_predictions[dev_predictions.model == selected]), ("holdout", holdout_predictions)]:
        frame = frame.copy()
        frame["risk_level"] = risk_tiers(frame.probability, thresholds)
        grouped = frame.groupby("risk_level").agg(accounts=("label", "size"), observed_inactivity=("label", "mean"), value_proxy=("value_proxy", "sum"))
        tier_rows.append(grouped.reset_index().assign(split=split))
    seg = test.copy()
    seg["probability"] = p
    seg["segment"] = pd.cut(seg.historical_order_count, [9, 19, 49, np.inf], labels=["10–19", "20–49", "50+"])
    segment_metrics = pd.DataFrame([{ "segment": str(k), **evaluate(v.label, v.probability, v.historical_spend, thresholds["binary"])}
                                  for k, v in seg.groupby("segment", observed=True)])
    activity_rows = []
    for label, mask in [("Ordered within last 60 days", seg.days_since_last_order <= 60),
                        ("Already inactive over 60 days", seg.days_since_last_order > 60)]:
        subset = seg[mask]
        if len(subset):
            activity_rows.append({"current_activity": label,
                                  **evaluate(subset.label, subset.probability, subset.historical_spend, thresholds["binary"])})
    return {"selected_model": selected, "best_pr_auc_model": best, "thresholds": thresholds,
            "metrics": pd.DataFrame(metrics), "predictions": pd.concat([dev_predictions, holdout_predictions]),
            "manifests": manifests, "importance": importance_table,
            "reliability": reliability_table(test.label, p), "deciles": decile_table(test.label, p, test.historical_spend),
            "tier_metrics": pd.concat(tier_rows), "segment_metrics": segment_metrics, "activity_metrics": pd.DataFrame(activity_rows)}
