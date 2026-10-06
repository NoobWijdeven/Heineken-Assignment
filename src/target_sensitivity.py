"""Compare predictability of alternative targets on development dates only."""
import pandas as pd
from .config import DEV_CUTOFFS
from .churn_labels import build_labels
from .train_model import train_model, temporal_training_split
from .evaluate import evaluate


def target_sensitivity(data, snapshots):
    results = []
    for target in ["inactivity_60d", "inactivity_90d", "frequency_decline_60d", "cadence_inactivity"]:
        frames = []
        for date, features in snapshots.items():
            eligible = features[features.model_eligible]
            if not eligible.empty:
                frames.append(eligible.merge(build_labels(data, eligible, target), on="account_id").dropna(subset=["label"]))
        labelled = pd.concat(frames, ignore_index=True)
        for cutoff in DEV_CUTOFFS:
            val = labelled[labelled.analysis_date == cutoff]
            if val.label.nunique() < 2:
                continue
            fit, cal = temporal_training_split(labelled, cutoff)
            for name in ["recency_baseline", "cadence_baseline", "logistic"]:
                model = train_model(name, fit, cal)
                p = model.predict(val)
                results.append({"definition": target, "cutoff": cutoff, "model": name,
                                "fit_rows": len(fit), "calibration_rows": len(cal),
                                **evaluate(val.label, p, val.historical_spend)})
    return pd.DataFrame(results)
