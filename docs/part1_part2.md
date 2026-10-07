# Parts 1 and 2: who is slipping away, and who do we help first?

## Part 1 (Identify): which customers are about to leave?

**Evidence status:** this page describes the supplied Ritmo prototype exports, which use a separate model from Account Compass. Ritmo's generation scripts, held-out predictions and validation reports are not in this repository. Reported results below remain unverified until those materials are added. Reproducible Account Compass results are documented in [METHODOLOGY.md](METHODOLOGY.md) and [results/model_summary.md](results/model_summary.md).

- **Target:** no order in the next **60 days**. This is future inactivity, not confirmed permanent loss. Current inactivity is shown separately. Ritmo's reported median gap of 22 days and roughly 25% non-return within six months require supporting cohort definitions and validation outputs.
- **Customers with only 1 or 2 orders** receive no modelled Ritmo probability or priority rank. The supplied exports assign some to WhatsApp drafts and others to Monitor. Sparse accounts remain visible without interpreting missing risk as zero.
- **Who is scored:** every customer with 3+ orders (9,735), using their order history up to 31 Aug 2018.
- **Warning signs we found:**
  - ordering less often than the quarter before
  - being quiet for longer than their own normal rhythm
  - spending less than the quarter before
  - stopping a frequently purchased product line (Ritmo reports 2 to 2.6x risk; supporting analysis is pending)
  - having only a few orders in total (a "thin relationship")
- Ritmo supplies a separate **60-day risk estimate** and plain-language observations. Its training, calibration and temporal leakage checks cannot be reproduced here yet.
- Delivery and review observations can inform a conversation. The existing Identify analysis does not establish whether either causes inactivity.
- **Reported performance, unverified:** Ritmo reports ROC-AUC 0.74 versus a recency baseline of 0.58 for still-ordering accounts. Matching population, horizon, cutoffs and held-out predictions are needed before comparing this with Account Compass's measured results.

## Part 2 (Prioritise): who gets help first?

**Exported priority = historical annual merchandise-value proxy × supplied risk estimate × saveability weight.**

Ritmo reports weights from 1.0 for under 30 days of inactivity to about 0.77 for 120+ days. Their derivation is not included. Historical return behaviour alone does not establish the benefit of an intervention, so these are prototype weights rather than verified probabilities of saving an account. The supplied channel allocation is:

1. **Rep visit:** the 150 most important *regular* customers (5+ orders), as weekly routes per state (12 visits a week).
2. **AI phone call:** the next 850.
3. **WhatsApp offer:** about 7,000 other at-risk and new customers.
4. **Keep an eye on:** everyone else.

**Reported performance, unverified:** Ritmo reports 29% versus 8% of its historical lost-value measure in the top 1,000 (described as about 3.5 times). Its evaluation code, value definition and cutoff-specific results are needed to verify that comparison. The app displays the supplied rank, risk estimate and observations.

## Real examples

These are exported challenge accounts, not HEINEKEN customers. Percentages are rounded; priority uses unrounded underlying estimates, so displayed multiplications are approximate. Product categories represent hypothetical portfolio lines. Route sequences are illustrative and do not incorporate road travel times.

| Customer | Facts | Why flagged | Score | Result |
| --- | --- | --- | --- | --- |
| **A24220 Niterói** (demo) | 64 orders, normally every 7 days, spent 6,802 last year | Stopped buying sports_leisure (7 months running); quiet 26 days; spend down 57%; orders 4 → 1 per quarter | 6,802 × 24% × 1.0 = 1,605 | **#17, rep visit**, RJ route week 1. Talking point: 1-star review in May |
| **A20080 Rio** | 7 orders, normally every 61 days, spent 13,697 | Orders 2 → 0 per quarter; quiet 102 days; spend down 100% | 13,697 × 55% × 0.81 = 6,180 | **#1, rep visit** |
| **A48602 Paulo Afonso** | 5 orders, spent 1,263 | Orders 2 → 0; only 5 orders in 17 months | 60% chance | **#663, AI call** |
| **A70255 Brasília** | 4 orders, spent 419, quiet 184 days | Thin relationship; far past its 50-day rhythm | 75% chance, but little money | **#4,496, WhatsApp offer** |
| **A77020 Palmas** | 11 orders, spent 1,603 | Spend down 81%; orders 4 → 1 per quarter | 33% chance, modest money | **#1,006, Monitor**: warning signs, but not yet worth a call |

So a high chance of leaving alone isn't enough (Brasília), and a low chance can still mean a visit when a lot of money is at stake (Niterói). This week's rep routes: São Paulo 43 visits, Minas Gerais 21, Rio de Janeiro 16, plus smaller states.

## How this fits Account Compass

Demian's 60-day score shows as "how likely to stop", but only for the 2,611 customers with 10+ orders. Ritmo adds the rank, the lane, the route and the plain-word reasons for all 9,735. Both now use the same 60-day window. The two percentages still come from different models, so the app labels them separately: "Account Compass 60-day forecast" and Ritmo's "chance of going silent for 60 days".

Ritmo's outputs used by the app are in `demo_data/ritmo/` (`priority_list.csv`, `lane_a_routes.csv`).
