# Dataset setup

Extract the eight challenge CSVs here, with their original filenames. No nested ZIP folder is expected. Use `python -m src.score_accounts` from the repository root. All IDs are loaded as strings. These files are ignored by Git; share the assignment dataset separately with collaborators.

The loader requires order_lines.csv, orders.csv, customers.csv, order_items.csv, order_payments.csv, order_reviews.csv, products.csv and geolocation.csv. The denormalised table supplies purchase-time categories/item values, while original orders and reviews supply precise event timestamps.
