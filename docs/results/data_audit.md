# Source data audit

Source: the eight supplied challenge CSVs.
Scoring date: 2018-08-31.

| File | Rows | Columns |
|---|---:|---:|
| order_lines.csv | 103,646 | 17 |
| orders.csv | 90,961 | 9 |
| customers.csv | 90,961 | 6 |
| order_items.csv | 102,942 | 5 |
| order_payments.csv | 95,048 | 5 |
| order_reviews.csv | 90,263 | 7 |
| products.csv | 32,951 | 9 |
| geolocation.csv | 19,010 | 6 |

- Distinct orders: 90,961; accounts: 14,989.
- Purchase range: 2017-01-05 to 2018-08-31.
- Duplicate order keys: 0.
- Duplicate (order_id, order_item_id) keys: 0.
- Review answers after cutoff: 558.
- Deliveries after cutoff: 48.
- Orders without priced lines: 704.
- Canonical and denormalised account/order maps and purchase dates agree.
- All IDs loaded as text. Every account with a purchase is preserved.

## Order-history segments

| Orders | Accounts |
|---|---:|
| 1 | 3,032 |
| 2–4 | 5,664 |
| 5–9 | 3,682 |
| 10+ | 2,611 |

## Final recorded statuses (audit only)

| Status | Orders |
|---|---:|
| delivered | 88,283 |
| shipped | 992 |
| unavailable | 579 |
| canceled | 534 |
| processing | 291 |
| invoiced | 275 |
| created | 5 |
| approved | 2 |

## Missingness in denormalised lines

| Field | Missing fraction |
|---|---:|
| account_id | 0.000% |
| city | 0.000% |
| state | 0.000% |
| order_id | 0.000% |
| order_date | 0.000% |
| order_month | 0.000% |
| order_status | 0.000% |
| order_item_id | 0.679% |
| product_id | 0.679% |
| product_category | 0.679% |
| price | 0.679% |
| freight_value | 0.679% |
| delivered_date | 2.822% |
| estimated_delivery_date | 0.000% |
| days_late | 2.822% |
| is_late | 2.822% |
| review_score | 0.841% |

## Interpretation and timestamp policy

Orders are placed-order events, including eventual cancellations/unavailability. Final status has no event timestamp and is never used to filter historical features or labels.
Spend is quoted merchandise value (sum of item prices), excluding freight. It is a relative value proxy, not realised revenue or currency.
The joined review score and joined delivery flags are deliberately ignored: original answer/delivery timestamps govern availability.
Calendar-day cutoffs include the whole day. Missing service/review evidence remains missing, rather than becoming a favourable score.
All eight CSVs are audited. Payments, product dimensions and geolocation are not predictive inputs in v1.
