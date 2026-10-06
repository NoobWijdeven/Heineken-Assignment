import numpy as np
import pandas as pd
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_score,
                             recall_score, f1_score, confusion_matrix, brier_score_loss)


def evaluate(y, p, values, threshold=.5):
    y, p, values = np.asarray(y, int), np.asarray(p, float), np.asarray(values, float)
    predicted = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    order = np.argsort(-p, kind="stable")
    top100 = order[:min(100, len(y))]
    topdecile = order[:max(1, int(np.ceil(len(y) * .1)))]
    prevalence = y.mean()
    result = {"accounts": len(y), "prevalence": prevalence,
              "roc_auc": roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan,
              "pr_auc": average_precision_score(y, p),
              "precision": precision_score(y, predicted, zero_division=0),
              "recall": recall_score(y, predicted, zero_division=0),
              "f1": f1_score(y, predicted, zero_division=0),
              "threshold": threshold, "tn": tn, "fp": fp, "fn": fn, "tp": tp,
              "brier": brier_score_loss(y, p),
              "brier_prevalence_baseline": float(np.mean((y - prevalence) ** 2)),
              "precision_at_100": y[top100].mean(), "positives_at_100": int(y[top100].sum()),
              "top100_value_proxy": values[top100].sum(),
              "top_decile_lift": y[topdecile].mean() / prevalence if prevalence else np.nan,
              "top_decile_positive_value_proxy": values[topdecile][y[topdecile] == 1].sum()}
    bins = pd.cut(p, np.linspace(0, 1, 11), include_lowest=True)
    frame = pd.DataFrame({"bin": bins, "label": y, "prediction": p})
    rel = frame.groupby("bin", observed=True).agg(n=("label", "size"), actual=("label", "mean"), predicted=("prediction", "mean"))
    result["calibration_ece"] = float((rel.n / len(y) * abs(rel.actual - rel.predicted)).sum())
    return result


def reliability_table(y, p):
    df = pd.DataFrame({"label": np.asarray(y, int), "predicted_probability": p})
    df["probability_bin"] = pd.cut(df.predicted_probability, np.linspace(0, 1, 11), include_lowest=True)
    return df.groupby("probability_bin", observed=True).agg(
        accounts=("label", "size"), mean_estimate=("predicted_probability", "mean"), observed_inactivity=("label", "mean")).reset_index()


def decile_table(y, p, values):
    df = pd.DataFrame({"label": np.asarray(y, int), "p": p, "value": values})
    df = df.sort_values("p", ascending=False, kind="stable").reset_index(drop=True)
    df["risk_decile"] = np.minimum((np.arange(len(df)) * 10 // len(df)) + 1, 10)
    result = df.groupby("risk_decile").agg(accounts=("label", "size"), positive_rate=("label", "mean"), value_proxy=("value", "sum"))
    result["lift"] = result.positive_rate / df.label.mean()
    return result.reset_index()


def risk_tiers(probabilities, thresholds):
    return np.select([probabilities >= thresholds["high"], probabilities >= thresholds["medium"]], ["High", "Medium"], default="Low")


def select_thresholds(dev_predictions):
    p, y = dev_predictions.probability.to_numpy(), dev_predictions.label.to_numpy()
    grid = np.unique(np.quantile(p, np.linspace(.05, .95, 91)))
    best = max(grid, key=lambda t: f1_score(y, p >= t, zero_division=0))
    return {"binary": float(best), "medium": float(np.quantile(p, .75)), "high": float(np.quantile(p, .9))}
