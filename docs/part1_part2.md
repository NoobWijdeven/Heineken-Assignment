# Parts 1 and 2: who is slipping away, and who do we help first?

## Part 1 (Identify): which customers are about to leave?

- **When is a customer gone?** When they haven't ordered for **60 days**, the same window as the Account Compass forecast. Regular customers order about every 3 weeks (median 22 days), so that's about 3 missed orders. Of shops already silent for 60 to 90 days, about 1 in 4 never come back within half a year.
- **Customers with only 1 or 2 orders** have no habit yet, so we don't score them. They get a WhatsApp message.
- **Who is scored:** every customer with 3+ orders (9,735), using their order history up to 31 Aug 2018.
- **Warning signs we found:**
  - ordering less often than the quarter before
  - being quiet for longer than their own normal rhythm
  - spending less than the quarter before
  - stopping a product they always bought, which is the strongest sign (2 to 2.6x more risk)
  - having only a few orders in total (a "thin relationship")
- A model that learned from past data combines these signs into a **chance of leaving in the next 60 days**. Each customer also gets the signs that apply to them, written in plain words.
- **Surprise:** late deliveries and bad reviews do **not** make customers leave. We use them only as something for the rep to talk about.
- **Does it work?** Tested on past data: for customers who are still ordering, our score is much better at spotting who will leave than "days since last order" (0.74 vs 0.58, where 0.5 is guessing).

## Part 2 (Prioritise): who gets help first?

**Priority = money spent in the last 12 months × chance of leaving × chance we can still win them back.**

The last part comes from history: a customer quiet for under 30 days counts fully (1.0), and one quiet for 120+ days counts 0.77. The highest priority gets help first, through the lane that fits:

1. **Rep visit:** the 150 most important *regular* customers (5+ orders), as weekly routes per state (12 visits a week).
2. **AI phone call:** the next 850.
3. **WhatsApp offer:** about 7,000 other at-risk and new customers.
4. **Keep an eye on:** everyone else.

**Does it work?** On past data, our list caught **3.5 times more lost money** (29% vs 8% in the top 1,000) than a list based only on "who is most likely to leave". The rep sees a rank, the chance of leaving in %, and the reasons in plain words.

## Real examples

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
