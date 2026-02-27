# Sales ORM Optimization Demo

This project demonstrates the difference between a costly ORM usage and an optimized approach when generating CSV reports.

## Domain Model

- `Reseller` is linked to Django `User` with `OneToOneField`.
- `Product` has a many-to-many relation with `Category`.
- `Sale` contains multiple `SaleItem` rows.
- `SaleItem` stores `category`, `quantity`, `unit_price`, and `line_total` snapshot fields.

## Seed Data

Use the management command to create a high-volume dataset:

```bash
python manage.py seed_sales
```

Default volume:

- 1,000 users/resellers
- 80 categories
- 10,000 products
- 100,000 sales
- 2 to 4 items per sale (~300,000 sale items average)

Useful options:

```bash
python manage.py seed_sales --reset
python manage.py seed_sales --sale-count 200000 --chunk-size 8000
```

## APIs

### 1) Non-optimized CSV report

Endpoint:

- `GET /sales/reports/unoptimized`

Characteristics:

- Makes relational reads inside Python loops.
- Triggers N+1 queries intentionally.
- Builds and returns full CSV in memory.
- Useful to demonstrate bottlenecks.

### 2) Optimized CSV streaming report

Endpoint:

- `GET /sales/reports/optimized`

Characteristics:

- Uses `select_related` and `prefetch_related` to reduce extra queries.
- Uses `values_list` to fetch only required columns.
- Streams CSV rows with `StreamingHttpResponse`.
- Reduces memory pressure for large exports.

## Why this matters

For large datasets, optimization patterns in Django ORM have direct impact on:

- Query count
- Response time
- Memory usage during export

This repository is designed so both implementations produce the same CSV schema and can be benchmarked side by side.

## Dependency Safety Note

- Use `djangorestframework` (official package).
- Avoid `django-restframework` (look-alike/typosquatting style package name).
- Verify installed dependencies with `uv pip list`.
