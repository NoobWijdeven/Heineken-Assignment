from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from .config import FEATURES, SEED


def logit(p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


@dataclass
class RiskModel:
    name: str
    features: list
    estimator: Pipeline
    calibration: object
    calibration_prior: float
    fit_cutoffs: list
    calibration_cutoff: str

    def predict(self, frame):
        raw = self.estimator.predict_proba(frame[self.features])[:, 1]
        if self.calibration is None:
            return np.repeat(self.calibration_prior, len(frame))
        return self.calibration.predict_proba(logit(raw))[:, 1]


def train_model(name, fit, calibration):
    if name == "recency_baseline":
        features = ["days_since_last_order"]
    elif name == "cadence_baseline":
        features = ["cadence_ratio"]
    else:
        features = FEATURES
    if name in ["recency_baseline", "cadence_baseline", "logistic"]:
        clf = LogisticRegression(C=1, max_iter=3000, random_state=SEED)
    elif name == "random_forest":
        clf = RandomForestClassifier(n_estimators=150, max_depth=6, min_samples_leaf=20, random_state=SEED, n_jobs=2)
    elif name == "gradient_boosting":
        clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=7, min_samples_leaf=25, l2_regularization=3, random_state=SEED)
    else:
        raise ValueError(name)
    estimator = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("scale", StandardScaler()), ("classifier", clf),
    ])
    if len(fit) < 50 or fit.label.nunique() != 2:
        raise ValueError("Insufficient matured training labels for a binary model")
    estimator.fit(fit[features], fit.label.astype(int))
    raw = estimator.predict_proba(calibration[features])[:, 1]
    prior = float(calibration.label.mean())
    sigmoid = None
    if calibration.label.nunique() == 2:
        sigmoid = LogisticRegression(C=1, max_iter=1000, random_state=SEED)
        sigmoid.fit(logit(raw), calibration.label.astype(int))
        # A negative slope would reverse the model ordering on a small/noisy sample.
        # Record a prevalence-only fallback instead of implying predictive ability.
        if sigmoid.coef_[0, 0] <= 0:
            sigmoid = None
    return RiskModel(name, features, estimator, sigmoid, prior,
                     sorted(fit.analysis_date.unique().tolist()), calibration.analysis_date.iloc[0])


def temporal_training_split(labelled, decision_date):
    """All outcomes mature before decision; fit outcomes mature before calibration features."""
    T = pd.Timestamp(decision_date)
    mature = labelled[pd.to_datetime(labelled.label_end_date) <= T].copy()
    if mature.empty:
        raise ValueError(f"No matured training labels by {decision_date}")
    calibration_date = mature.analysis_date.max()
    calibration = mature[mature.analysis_date == calibration_date]
    fit = mature[pd.to_datetime(mature.label_end_date) <= pd.Timestamp(calibration_date)]
    fit = fit[fit.analysis_date < calibration_date]
    assert pd.to_datetime(fit.label_end_date).max() <= pd.Timestamp(calibration_date)
    assert pd.to_datetime(calibration.label_end_date).max() <= T
    if fit.empty or calibration.empty:
        raise ValueError("Temporal purge leaves insufficient history")
    return fit, calibration
