# Fictional collaboration fixtures

All 12 accounts, purchase histories, values and risk probabilities in this folder are synthetic. No real challenge account records are included. Risk values and tier thresholds are fabricated demonstration values; do not use them in model validation or describe them as measured predictions.

The CSV has the same columns as `outputs/scored_accounts.csv`; IDs begin with DEMO. Regenerate with `python -m src.make_demo`. Nullable probabilities demonstrate sparse-account handling. The default dashboard uses this folder when real outputs are absent.
