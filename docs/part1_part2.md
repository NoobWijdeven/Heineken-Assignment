# Parts 1 and 2: who is slipping away, and who do we help first?

## Part 1 (Identify): which customers are about to leave?

- **When is a customer gone?** When they haven't ordered for **90 days**. Regular customers order about every 3 weeks, so that's about 4 missed orders. After 90 days of silence, more than a quarter never come back.
- **Customers with only 1 or 2 orders** have no habit yet, so we don't score them. They get a WhatsApp message.
- **Who is scored:** every customer with 3+ orders (9,735), using their order history up to 31 Aug 2018.
- **Warning signs we found:**
  - ordering less often than the quarter before
  - being quiet for longer than their own normal rhythm
  - spending less than the quarter before
  - stopping a product they always bought, which is the strongest sign (3.5x more risk)
  - having only a few orders in total (a "thin relationship")
- A model that learned from past data combines these signs into a **chance of leaving in the next 90 days**. Each customer also gets the signs that apply to them, written in plain words.
- **Surprise:** late deliveries and bad reviews do **not** make customers leave. We use them only as something for the rep to talk about.
- **Does it work?** Tested on past data: for customers who are still ordering, our score is much better at spotting who will leave than "days since last order" (0.73 vs 0.58, where 0.5 is guessing).

## Part 2 (Prioritise): who gets help first?

**Priority = money spent in the last 12 months × chance of leaving × chance we can still win them back.**

The last part comes from history: a customer quiet for under 30 days counts fully (1.0), and one quiet for 120+ days counts 0.77. The highest priority gets help first, through the lane that fits:

1. **Rep visit:** the 150 most important *regular* customers (5+ orders), as weekly routes per state (12 visits a week).
2. **AI phone call:** the next 850.
3. **WhatsApp offer:** about 6,900 other at-risk and new customers.
4. **Keep an eye on:** everyone else.

**Does it work?** On past data, our list caught **3 times more lost money** than a list based only on "who is most likely to leave". The rep sees a rank, the chance of leaving in %, and the reasons in plain words.

## Real examples

| Customer | Facts | Why flagged | Score | Result |
| --- | --- | --- | --- | --- |
| **A24220 Niterói** (demo) | 64 orders, normally every 7 days, spent 6,802 last year | Stopped buying sports_leisure (7 months running); quiet 26 days; spend down 57%; orders 4 → 1 per quarter | 6,802 × 21% × 1.0 = 1,425 | **#13, rep visit**, RJ route week 1. Talking point: 1-star review in May |
| **A20080 Rio** | 7 orders, normally every 61 days, spent 13,697 | Orders 2 → 0 per quarter; quiet 102 days; spend down 100% | 13,697 × 44% × 0.81 = 4,923 | **#1, rep visit** |
| **A48602 Paulo Afonso** | 5 orders, spent 1,263 | Orders 2 → 0; only 5 orders in 17 months | 48% chance | **#609, AI call** |
| **A70255 Brasília** | 4 orders, spent 419, quiet 184 days | Thin relationship; far past its 50-day rhythm | 66% chance, but little money | **#3,476, WhatsApp offer** |
| **A21350 Rio** | 13 orders, spent 1,945 | Spend down 87% | Only 18% chance | **Monitor**: a warning sign, but still ordering normally |

So a high chance of leaving alone isn't enough (Brasília), and a low chance can still mean a visit when a lot of money is at stake (Niterói).

## How this fits Account Compass

Demian's 60-day score shows as "how likely to stop", but only for the 2,611 customers with 10+ orders. Ritmo adds the rank, the lane, the route and the plain-word reasons for all 9,735. The two percentages answer different questions (60 vs 90 days), so the app labels them separately: "Account Compass 60-day forecast" and "chance of going silent for 90 days".

Ritmo's outputs used by the app are in `demo_data/ritmo/` (`priority_list.csv`, `lane_a_routes.csv`).
