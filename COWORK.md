# HEINEKEN × AISO Challenge — CoWork Project Brief

## 1. Purpose of this file

This file is the operating brief for CoWork and all collaborators working on the HEINEKEN × AISO challenge.

The immediate priority is **Part 1 — Identify**: build a defensible, interpretable churn / account-risk prediction system and expose the results through a highly user-friendly interface so another teammate can build the **Act** layer on top of it.

The datasets will be added separately by the project owner. Do not assume they are present until they appear in the repository.

---

# 2. Challenge context

HEINEKEN sells to bars, restaurants, and shops through large sales teams. The desired role of the sales representative is not simply to take orders, but to act as a business advisor.

HEINEKEN already uses an AI system called **AIDDA (AI Data-Driven Advisor)** to recommend next-best actions for customers. According to the challenge brief, AIDDA increased sales by more than 5% in its first year in Mexico and supported about 490,000 customers across seven markets by 2024.

This student challenge is a simplified version of the same commercial problem.

## Core business problem

Sales representatives manage hundreds of accounts and may only see a customer a few times per year.

Accounts often do not disappear suddenly. Instead, deterioration can happen gradually:

- they order less frequently;
- spend declines;
- they stop buying product lines they previously bought;
- they skip expected ordering periods;
- they may have experienced a service issue such as a late delivery;
- satisfaction may fall before the account is visibly lost.

The challenge is therefore:

> **How can HEINEKEN identify at-risk accounts early, determine which accounts deserve attention first, and give the sales representative a useful next action?**

---

# 3. The three challenge stages

The challenge has three connected parts.

## Part 1 — Identify

Define what churn / account risk means in this dataset.

Determine which variables and behavioural patterns are predictive of future inactivity or deterioration.

The result must be justified with evidence rather than arbitrary thresholds.

## Part 2 — Prioritise

A representative cannot act on every warning.

Rank flagged accounts based on factors such as:

- churn / deterioration risk;
- account value;
- confidence in the signal;
- potentially recoverable value;
- actionability.

## Part 3 — Act

Turn the warning into something useful.

Examples from the challenge brief include:

- tailored offers;
- talking-point cards;
- call scripts;
- voice agents;
- account briefings;
- visit planners.

The submitted prototype is expected to demonstrate this action layer, but Parts 1 and 2 must clearly support it.

A key principle from the challenge brief:

> A simple, well-argued risk score with a strong action step is better than a sophisticated model that produces no useful action.

---

# 4. Submission context

The challenge submission consists of:

1. **A public demo link**
   - Must be openable by the jury without logging in.
   - Parts may be mocked up if the connection to the analysis is clear.

2. **A maximum 3-minute video**
   - Narrates the demo.
   - Explains the solution at the business level.
   - Production quality is not important.

3. **A 1-page summary**
   - churn definition;
   - main predictive signals;
   - prioritisation logic;
   - next steps.

The jury evaluates:

- business understanding;
- quality of analysis;
- prioritisation logic;
- action and creativity;
- quality of the demo.

The challenge explicitly values the connection between technology and business over unnecessary technical complexity.

---

# 5. Dataset context

The dataset is an adapted, anonymised transactional dataset.

It is **not HEINEKEN data**, but it contains behavioural patterns intended to resemble the business problem.

## Time period

Approximately 91,000 orders from:

- **January 2017**
- through **31 August 2018**

For all modelling and analysis:

> **Treat 31 August 2018 as “today”.**

No information after that date exists and no future information may be assumed.

## Account definition

The original dataset contains many individual buyers who order only once.

For this challenge:

> **Treat each ZIP-code area as one commercial account.**

The account key is:

`account_id`

It represents a hypothetical bar, restaurant, shop, or similar HEINEKEN customer.

Important dataset facts from the challenge documentation:

- 14,989 accounts in total;
- approximately 2,600 accounts have 10 or more orders;
- those repeat accounts generate approximately 52% of all orders;
- repeat accounts order across a median of roughly 10 different months;
- repeat accounts buy roughly 11 categories on median;
- small accounts often contain random gaps, so low activity alone must not automatically be interpreted as churn.

This last point is especially important for modelling.

---

# 6. Files expected in the dataset

The project owner will add the dataset separately.

Expected files:

```text
data/
├── order_lines.csv
├── orders.csv
├── customers.csv
├── order_items.csv
├── order_payments.csv
├── order_reviews.csv
├── products.csv
└── geolocation.csv
```

## Main recommended starting file

Use:

`order_lines.csv`

as the initial analytical table.

It already joins:

- orders;
- order items;
- products;
- customers;
- reviews.

### Important warning

`order_lines.csv` is at **product-line level**, not order level.

An order containing multiple products appears multiple times.

Therefore:

> **Never count rows as orders. Always count distinct `order_id`.**

Orders without products may still appear with empty product fields, particularly cancelled or unavailable orders.

---

# 7. Important variables

Typical fields in `order_lines.csv` include:

```text
account_id
city
state
order_id
order_date
order_month
order_status
order_item_id
product_id
product_category
price
freight_value
delivered_date
estimated_delivery_date
days_late
is_late
review_score
```

Other files provide:

### Orders
- order status;
- purchase timestamp;
- approval timestamp;
- carrier delivery timestamp;
- customer delivery timestamp;
- estimated delivery date.

### Customers
- customer ID;
- customer unique ID;
- account ID;
- ZIP code;
- city;
- state.

### Payments
- payment method;
- instalments;
- payment value.

### Reviews
- review score;
- Portuguese review title;
- Portuguese review comment;
- review timestamp.

### Products
- category;
- dimensions;
- weight;
- metadata.

### Geolocation
- account latitude;
- account longitude;
- city;
- state.

---

# 8. Data-handling rules

These rules are mandatory.

## 8.1 Keep account IDs as text

`account_id` and ZIP-code fields must remain strings.

Do not allow pandas, Excel, or another tool to convert them into integers because leading zeros may be lost and joins may break.

## 8.2 Avoid leakage

When pretending a historical date is “today”, use **only information known up to that date**.

No later orders, reviews, delivery events, category purchases, or outcomes may enter the feature calculation.

## 8.3 Treat product categories as behavioural categories

The product categories come from a general online marketplace.

Their literal names are irrelevant.

For this challenge interpret them as product lines in a beverage portfolio.

Example:

`health_beauty`

does **not** need to be interpreted literally.

The important signal is whether an account:

- buys a category regularly;
- stops buying it;
- adds or removes categories;
- narrows its purchasing breadth.

## 8.4 Monetary values

Treat monetary values as **relative commercial value**.

Do not attach a real currency interpretation unless explicitly required.

## 8.5 Dataset growth

Order volume grows strongly during 2017.

Do not interpret simple period-over-period growth as customer improvement without controlling for:

- account age;
- historical purchasing rhythm;
- differing observation windows;
- overall dataset growth.

---

# 9. Immediate project objective

The first deliverable is a complete **Identify system**.

It should answer:

1. Which accounts are currently at risk?
2. How risky is each account?
3. What evidence supports that assessment?
4. How confident are we in that assessment?
5. What behavioural change triggered the warning?
6. Can the result be consumed easily by a teammate building the Act layer?

The Identify system should be both:

- analytically defensible;
- easy to understand.

Avoid producing a black-box model that gives only a probability.

---

# 10. Core modelling principle

Do **not** begin by defining churn as a fixed number of inactive days.

A fixed rule such as:

> “No order for 90 days = churn”

may be too crude because accounts have different natural ordering rhythms.

A stronger concept to test is:

> **An account becomes risky when its current inactivity or decline is abnormal relative to its own historical purchasing behaviour.**

For example:

- Account A normally orders every 18–25 days and is now 65 days inactive.
- Account B normally orders every 70–90 days and is now 65 days inactive.

The same inactivity period should not necessarily produce the same risk.

This is a modelling hypothesis and must be tested, not assumed.

---

# 11. Required modelling strategy

The modelling work should proceed in stages.

## Stage A — Exploratory account profiling

Build one row per `account_id`.

At minimum calculate:

### Account history
- number of distinct orders;
- first order date;
- last order date;
- account age;
- active months;
- months with at least one order.

### Recency
- days since last order;
- days since second-to-last order;
- recency relative to analysis date.

### Ordering cadence
- median days between orders;
- mean days between orders;
- standard deviation of order gaps;
- coefficient of variation of order gaps;
- latest gap relative to median gap;
- latest gap relative to historical distribution.

Candidate feature:

```text
cadence_ratio =
days_since_last_order / median_historical_order_gap
```

Interpretation:

- around 1.0 = roughly on normal schedule;
- substantially above 1.0 = overdue relative to normal behaviour.

Do not assume the threshold; determine it empirically.

### Frequency
Compare recent purchasing frequency with historical behaviour.

Candidate windows:

- last 30 days;
- last 60 days;
- last 90 days;
- previous equivalent period;
- historical monthly average.

Examples:

```text
orders_last_90d
orders_previous_90d
frequency_change_90d
```

### Spend / commercial value

Calculate:

- total historical spend;
- average spend per order;
- spend in last 30/60/90 days;
- spend in previous comparable period;
- spend change;
- estimated annualised account value where appropriate.

Avoid double counting line-level values.

### Category behaviour

Calculate:

- total unique categories historically;
- categories purchased recently;
- historically regular categories;
- categories dropped recently;
- category concentration;
- category breadth change.

A useful candidate definition:

> A “dropped category” is a category purchased repeatedly or consistently in the historical window but absent from the recent expected purchasing window.

The exact rule must be tested and documented.

### Service quality

Calculate:

- late-delivery count;
- late-delivery rate;
- average `days_late`;
- recent late-delivery events;
- change in delivery performance.

### Reviews / satisfaction

Calculate:

- average review score;
- latest review score;
- recent average review score;
- review trend;
- count of negative reviews;
- potentially relevant review text.

Portuguese comments may later be summarised or classified with an LLM, but review-text NLP is optional for the first modelling iteration.

### Confidence / evidence quality

Calculate variables such as:

- total order count;
- months observed;
- number of order gaps available;
- amount of recent evidence.

This is important because risk estimates for an account with 2 orders should not be treated with the same confidence as an account with 40 orders.

---

# 12. Account segmentation before modelling

Do not blindly apply the same model to every account.

At minimum inspect segments such as:

```text
1 order
2–4 orders
5–9 orders
10+ orders
```

The documentation explicitly indicates that low-order accounts contain substantial random gaps.

Possible modelling strategy:

- use established repeat accounts for the main churn prediction model;
- create a separate low-confidence treatment for sparse accounts;
- expose model confidence in the interface.

Do not silently exclude accounts.

If a segment is not modelled, document why.

---

# 13. Churn / deterioration definition

The final churn definition has to be justified empirically.

Do not hard-code a definition before testing.

Test multiple candidate target definitions.

Possible candidates include:

## Candidate A — Future inactivity

At historical cutoff date `T`:

```text
churn = no order during next N days
```

Candidate N values:

- 60 days;
- 90 days;
- potentially cadence-adjusted horizons.

## Candidate B — Severe frequency decline

Example:

```text
future_order_frequency
<
50% of historical expected frequency
```

## Candidate C — Commercial deterioration

Possible combination of:

- future inactivity;
- severe spend decline;
- loss of previously regular categories.

## Candidate D — Cadence-relative churn

Define failure based on an account substantially exceeding its normal expected reorder interval.

This may better reflect accounts with very different purchasing patterns.

### Required behaviour

CoWork should:

1. implement several candidate churn definitions;
2. compare them;
3. report how many accounts each labels;
4. inspect whether labels are commercially plausible;
5. determine which definition gives the clearest business interpretation and strongest predictive signal.

Do not choose solely based on model accuracy.

---

# 14. Temporal back-testing

This is mandatory.

Do not use a random train/test split as the primary validation method.

The model concerns future behaviour over time, so validation must simulate the real decision.

Example historical cutoffs:

```text
2018-03-31
2018-04-30
2018-05-31
```

For each cutoff:

1. pretend the cutoff is “today”;
2. calculate all features using data available only up to that date;
3. calculate the outcome using data after the cutoff;
4. evaluate predictions;
5. repeat for multiple cutoffs.

The final production scoring date is:

```text
2018-08-31
```

At that point there is no future label available, so use the model trained and validated on historical cutoffs to generate present-day risk estimates.

---

# 15. Baseline before advanced modelling

Always build an interpretable baseline first.

Candidate baseline components:

- cadence break;
- recency;
- frequency decline;
- spend decline;
- category dropout;
- negative recent review;
- recent delivery problems;
- confidence / account maturity.

Example conceptual score:

```text
risk_score =
    recency_component
  + cadence_component
  + frequency_component
  + spend_component
  + category_component
  + service_component
```

Do not use arbitrary weights without testing.

The purpose of the baseline is to create a transparent benchmark.

---

# 16. Candidate machine-learning models

After the baseline works, compare it with a small set of models.

Recommended candidates:

1. Logistic Regression
2. Random Forest
3. Gradient Boosting / XGBoost / LightGBM if dependencies allow

Avoid unnecessary deep learning.

The dataset is tabular and the submission values explanation and usability.

For each model compare:

- predictive performance;
- stability across historical cutoffs;
- interpretability;
- ease of explaining predictions;
- ease of deployment;
- incremental improvement over the baseline.

If a complex model produces only marginal improvement, prefer the simpler model.

---

# 17. Evaluation metrics

Accuracy is not sufficient because the target may be imbalanced.

At minimum calculate:

- ROC-AUC;
- PR-AUC;
- precision;
- recall;
- F1;
- confusion matrix;
- lift in top-risk deciles;
- calibration if probabilities are presented as percentages.

Most importantly, calculate commercial prioritisation metrics.

Example:

> Of the top 100 accounts flagged by the model, how many actually deteriorated during the historical back-test?

Also examine:

> How much historical/recent account value is represented in the top-risk group?

The model is meant to help a representative spend scarce time efficiently.

---

# 18. Risk is not the same as priority

Keep these concepts separate.

## Risk

Probability / evidence that the account is deteriorating.

## Value

Commercial importance of the account.

## Confidence

How trustworthy the prediction is given the amount and consistency of historical data.

## Priority

A later decision layer combining those concepts.

Example conceptual structure:

```text
priority ≈ risk × commercial_value × confidence
```

Do not finalise Part 2 prematurely, but design Part 1 outputs so this calculation becomes easy.

---

# 19. Explainability requirement

Every account prediction must have human-readable reasons.

Do not expose only:

```text
risk_probability = 0.82
```

Generate explanations such as:

```text
HIGH RISK

Why:
- Usually orders every 24 days
- Now 61 days since last order
- Order frequency is down 42%
- Spend over the last 90 days is down 57%
- 2 previously regular categories disappeared
- Latest review score was 2/5
```

The explanation should distinguish:

- strong evidence;
- supporting evidence;
- low-confidence signals.

For machine-learning models use feature contributions where practical, e.g.:

- coefficients for logistic regression;
- permutation importance;
- SHAP values if appropriate and lightweight.

Do not overwhelm the end user with technical model terminology.

---

# 20. Required handoff table

The Identify pipeline must export a clean account-level table for other teammates.

Preferred file:

```text
outputs/scored_accounts.csv
```

Minimum recommended schema:

```text
account_id
city
state

risk_probability
risk_score
risk_level
model_confidence

historical_order_count
active_months
first_order_date
last_order_date
days_since_last_order

median_order_gap_days
cadence_ratio

orders_last_30d
orders_last_60d
orders_last_90d
frequency_change

historical_spend
spend_last_90d
spend_change

historical_category_count
recent_category_count
categories_dropped_count
categories_dropped

avg_review_score
latest_review_score

late_delivery_rate
recent_late_delivery

top_risk_reason_1
top_risk_reason_2
top_risk_reason_3

model_version
analysis_date
```

Add fields if useful, but avoid unnecessary noise.

The Act layer should be able to consume this file without knowing the underlying modelling code.

---

# 21. User interface for Part 1

Build a lightweight, polished interface.

Recommended technology:

> **Streamlit**

The objective is not to build the final HEINEKEN application.

The objective is to create an intuitive decision surface that another teammate can build upon.

## Main page

Display:

### KPI strip
- number of accounts analysed;
- number high risk;
- number medium risk;
- value represented by high-risk accounts;
- average model confidence.

### Account table

Sortable / filterable columns:

```text
Account
Risk
Confidence
Account Value
Days Since Last Order
Cadence Ratio
Spend Change
Frequency Change
Categories Dropped
Top Risk Reason
```

Allow filters such as:

- risk level;
- state;
- minimum account value;
- minimum order count;
- confidence.

## Account detail page / panel

When an account is selected, show:

### Header
```text
Account A01037
HIGH RISK — 82%
Confidence: High
```

### Why the account is at risk

Human-readable explanation cards.

### Behaviour over time

Charts for:

1. order frequency over time;
2. spend over time;
3. days between orders;
4. categories purchased over time;
5. optionally review / service history.

### Account summary

Show:

- total historical orders;
- account tenure;
- typical ordering cadence;
- latest inactivity;
- historical value;
- recent spend change;
- categories lost;
- delivery quality;
- review quality.

### Handoff area

Include a clear placeholder:

```text
Recommended Action
[ To be connected to teammate's Act layer ]
```

The teammate should later be able to use the selected account record as input to their solution.

---

# 22. UI design principles

The interface should feel like a tool for a sales representative, not a data-science notebook.

Prioritise:

- clean spacing;
- obvious hierarchy;
- minimal technical jargon;
- concise explanations;
- high signal-to-noise;
- clear risk and confidence labels;
- charts that answer business questions;
- fast account navigation.

Avoid:

- raw dataframe dumps;
- dozens of plots;
- excessive statistical terminology;
- model-debugging information in the main UI.

Technical model diagnostics should be available separately if useful.

---

# 23. Repository architecture

Use a modular repository.

Recommended structure:

```text
heineken-churn-copilot/
│
├── COWORK.md
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   └── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── load_data.py
│   ├── clean_data.py
│   ├── build_features.py
│   ├── churn_labels.py
│   ├── backtest.py
│   ├── baseline.py
│   ├── train_model.py
│   ├── evaluate.py
│   ├── explain.py
│   └── score_accounts.py
│
├── app/
│   └── streamlit_app.py
│
├── notebooks/
│   └── 01_exploration.ipynb
│
├── outputs/
│   ├── scored_accounts.csv
│   ├── model_metrics.csv
│   └── feature_summary.csv
│
├── models/
│
└── tests/
```

---

# 24. Coding principles

## Modularise final logic

Exploration may happen in notebooks.

Production logic must move into reusable Python files.

Avoid a single giant notebook containing the complete solution.

## Reproducibility

A collaborator should be able to run:

```bash
pip install -r requirements.txt
```

and then an obvious pipeline command or script.

Prefer a simple workflow such as:

```bash
python -m src.score_accounts
streamlit run app/streamlit_app.py
```

Document exact commands in the README.

## Configuration

Keep important settings in one place:

```python
ANALYSIS_DATE = "2018-08-31"
```

Candidate churn horizon, feature windows, and model paths should also be centrally configurable.

## Determinism

Set random seeds where appropriate.

## Tests

Add lightweight tests for high-risk mistakes such as:

- duplicate order counting;
- leakage across cutoff dates;
- account ID datatype;
- date-window calculations;
- aggregation errors.

---

# 25. GitHub collaboration workflow

GitHub is the source of truth.

Recommended branches:

```text
main
demian/identify-model
teammate/action-layer
teammate/demo-integration
```

Rules:

1. Keep `main` stable.
2. Work on feature branches.
3. Commit small logical changes.
4. Use descriptive commit messages.
5. Merge through pull requests where practical.
6. Do not overwrite another teammate's work.
7. Preserve the output contract of `scored_accounts.csv`.

If the output schema changes, document it immediately.

---

# 26. Parallel collaboration strategy

The teammates should not need to wait for the final model.

As soon as the repository is set up:

1. create a **mock version** of `scored_accounts.csv`;
2. populate it with several fictional / temporary records;
3. allow the teammate building the Act layer to develop against that schema;
4. later replace the mock predictions with real model outputs.

The schema should remain stable.

This allows:

```text
Identify development
        ↓
scored_accounts.csv

and

Act development
        ↑
mock scored_accounts.csv
```

to happen simultaneously.

---

# 27. First implementation sequence

CoWork should execute the project in this order.

## Phase 1 — Scaffold

Create:

- repository structure;
- requirements;
- configuration;
- README;
- data-loading placeholders;
- mock scored account output;
- initial Streamlit shell.

Do not wait for modelling to build the basic app shell.

## Phase 2 — Data audit

Once datasets are added:

- verify filenames;
- inspect shapes;
- inspect columns;
- inspect missing values;
- verify unique keys;
- verify order duplication at line level;
- inspect date ranges;
- inspect order statuses;
- confirm account counts;
- confirm account ID types.

Produce a concise audit report.

## Phase 3 — Account feature table

Generate:

```text
outputs/account_features.csv
```

with one row per account.

Validate aggregations carefully.

## Phase 4 — Historical labels

Implement multiple churn definitions.

Create cutoff-specific training datasets.

## Phase 5 — Baseline

Build the interpretable risk baseline.

Evaluate via temporal back-tests.

## Phase 6 — Machine-learning comparison

Train a small set of interpretable tabular models.

Compare against baseline.

## Phase 7 — Select model

Choose the final model based on:

- predictive quality;
- stability;
- interpretability;
- business usefulness.

Document why.

## Phase 8 — Production scoring

Score accounts as of:

```text
2018-08-31
```

Export:

```text
outputs/scored_accounts.csv
```

## Phase 9 — Interface

Connect real model outputs to Streamlit.

## Phase 10 — Handoff documentation

Update README with:

- model definition;
- churn definition;
- feature logic;
- validation results;
- limitations;
- how teammate consumes the outputs.

---

# 28. Questions the analysis must answer

The final Part 1 analysis should make it possible to answer clearly:

1. What exactly do we mean by churn or deterioration?
2. Why is this definition suitable for the dataset?
3. Which behavioural features predict it best?
4. Is recency more useful when adjusted for normal account cadence?
5. Does declining order frequency add predictive value?
6. Does declining spend add predictive value?
7. Does category dropout add predictive value?
8. Do late deliveries increase subsequent churn risk?
9. Do low review scores increase subsequent churn risk?
10. How does prediction quality differ by account history?
11. How reliable are predictions for low-order accounts?
12. Which model performs best under historical back-testing?
13. How much better is it than a simple baseline?
14. Can we explain every high-risk prediction to a salesperson?

---

# 29. Analysis outputs to preserve

Produce the following reusable files where possible:

```text
outputs/
├── data_audit.md
├── account_features.csv
├── churn_definition_comparison.csv
├── backtest_results.csv
├── model_metrics.csv
├── feature_importance.csv
├── scored_accounts.csv
└── model_summary.md
```

Do not expose sensitive or unnecessary raw data through a public demo.

---

# 30. Model summary requirements

`outputs/model_summary.md` should eventually contain:

## Churn definition
Plain-English definition.

## Why this definition was selected
Evidence from back-testing and business reasoning.

## Population
Which account segments the model applies to.

## Main predictive signals
Ranked list with business explanations.

## Model
Selected method and why.

## Validation
Temporal back-test results.

## Limitations
Examples:

- short dataset horizon;
- sparse accounts;
- anonymised marketplace data rather than real HEINEKEN data;
- potentially artificial account construction via ZIP code;
- dataset growth effects;
- absence of true sales-rep interaction data.

## Current scoring date

```text
31 August 2018
```

---

# 31. Model interpretation principles

Do not state causal relationships unless the data supports causality.

For example:

Incorrect:

> “Late deliveries cause churn.”

Preferred:

> “Late deliveries are associated with higher subsequent churn risk in the historical sample.”

Similarly, feature importance does not prove causation.

The business interface may say:

> “Recent late delivery is a possible contributing signal.”

---

# 32. Data leakage checklist

Before accepting any model, explicitly verify:

- no future orders used in features;
- no future reviews used;
- no future delivery information used;
- no future category behaviour used;
- scaling / preprocessing fit only on training periods;
- target outcome clearly occurs after the prediction cutoff;
- duplicate order lines are not accidentally treated as separate orders.

This checklist must appear in technical documentation.

---

# 33. Quality bar for Part 1

Part 1 is considered ready for handoff when:

### Data
- one-row-per-account feature table exists;
- order counts are correct;
- account IDs remain strings;
- leakage checks pass.

### Churn definition
- at least two candidate definitions were tested;
- final definition is justified.

### Validation
- multiple historical cutoffs were used;
- baseline exists;
- selected model is compared with baseline.

### Model
- outputs risk score / probability;
- outputs confidence;
- outputs interpretable reasons.

### Handoff
- `scored_accounts.csv` exists;
- schema is documented;
- teammate can consume it without understanding modelling code.

### Interface
- account table is searchable/filterable;
- account detail view works;
- behaviour charts work;
- risk explanation is visible;
- action-layer placeholder exists.

### Documentation
- README explains how to run everything;
- model limitations are documented.

---

# 34. Important design decision: model confidence

Because account histories differ substantially, expose prediction confidence separately from risk.

Example:

```text
Risk: 89%
Confidence: Low
```

may occur when an account looks suspicious but has very little historical evidence.

Possible confidence factors:

- total order count;
- length of account history;
- number of observed reorder gaps;
- stability of historical cadence;
- completeness of review / service data.

Do not make confidence identical to model probability.

---

# 35. Possible risk-tier design

After calibration, consider:

```text
Low
Medium
High
Critical
```

Thresholds must be based on model outputs / business usefulness, not aesthetics.

For each tier show:

- number of accounts;
- historical validation precision;
- represented account value.

This will later support prioritisation.

---

# 36. Potential business narrative

A strong narrative for the solution is:

> Traditional churn rules ask whether a customer has not ordered for an arbitrary number of days. Our approach learns what normal purchasing behaviour looks like for each account. When that rhythm breaks, we look for corroborating signals such as declining order frequency, lower spend, category dropout, poor reviews, or delivery problems. The system then explains why the account is at risk so a sales representative can take action before the customer is lost.

Treat this as a narrative direction, not as a conclusion until analysis validates the underlying signals.

---

# 37. Things not to overbuild

Do not spend disproportionate time on:

- deep neural networks;
- complex MLOps;
- authentication;
- production databases;
- elaborate cloud infrastructure;
- perfect NLP translation;
- excessive geographic analysis;
- pixel-perfect enterprise UI.

The challenge rewards a convincing prototype and business logic.

---

# 38. Things worth spending time on

Prioritise:

1. correct temporal validation;
2. defensible churn definition;
3. strong features;
4. interpretable output;
5. excellent account-level explanation;
6. clear visual interface;
7. clean handoff to the Act layer;
8. compelling examples of real high-risk accounts.

---

# 39. Expected CoWork behaviour

CoWork should behave as an analytical engineering partner.

When implementing:

1. inspect before assuming;
2. preserve reproducibility;
3. document important choices;
4. flag uncertainty;
5. never silently change the agreed output schema;
6. avoid data leakage;
7. prefer simple solutions until complexity proves valuable;
8. keep the interface usable throughout development;
9. commit logical milestones to Git;
10. leave clear handoff notes for human collaborators.

If a modelling decision is uncertain, implement comparison tests rather than choosing arbitrarily.

---

# 40. First task for CoWork

Once this file is read, begin with the following task:

> **Scaffold the repository for the HEINEKEN churn-risk project and prepare it for collaborative development. Build the modular Python project structure, README, requirements file, configuration with analysis date 2018-08-31, data-loading placeholders, a mock `scored_accounts.csv` matching the handoff schema, and an initial Streamlit dashboard shell that can display and filter those mock accounts. Do not implement the final churn model before the real datasets are added. Make the architecture ready for temporal back-testing, feature engineering, model comparison, explainability, and easy integration with a teammate's Act layer.**

After the real datasets are added, proceed with the data audit and modelling sequence described above.

---

# 41. Final guiding principle

The output of Part 1 is not merely:

> “This account has an 82% churn probability.”

It should be:

> **“This account is at high risk, here is the behavioural evidence, here is how unusual the change is relative to its normal behaviour, here is how confident we are, and here is a clean structured record that another system can turn into an action.”**

That is the standard for the Identify layer.
