# Demo ORM: Unoptimized vs Optimized CSV Reports

This repository is a practical Django example for demonstrating ORM performance patterns in a LinkedIn post.

## What is included

- Domain models in English: `Reseller`, `Category`, `Product`, `Sale`, `SaleItem`
- High-volume seed command
- Two report endpoints (no authentication):
	- Non-optimized report (`N+1` style in Python loops)
	- Optimized report (`select_related`, `prefetch_related`, `values_list`, and streaming)

## Setup

```bash
uv sync
uv run python manage.py makemigrations
uv run python manage.py migrate
```

## Seed data

Default high volume (~100k sales / ~300k items average):

```bash
uv run python manage.py seed_sales
```

Reset and seed again:

```bash
uv run python manage.py seed_sales --reset
```

## Endpoints

- `GET /sales/reports/unoptimized`
- `GET /sales/reports/optimized`

Run server:

```bash
uv run python manage.py runserver
```

## Optimization write-up

See detailed explanation in:

- `docs/sales_optimization.md`
- `docs/sales_optimization_pt.md`

## Postman collection

Import this file in Postman to test both endpoints quickly:

- `docs/postman_collection_demo_orm.json`

Environment variable included in the collection:

- `base_url` (default: `http://127.0.0.1:8000`)

## Docker

This project includes Docker support with Django + MySQL.

Before building the image, refresh lockfile after dependency changes:

```bash
uv lock
```

### Start services

```bash
docker compose up --build
```

### Stop services

```bash
docker compose down
```

### Full reset (containers + volume)

```bash
docker compose down -v
docker compose up --build
```

### Endpoints in Docker

- `GET http://127.0.0.1:8000/sales/reports/unoptimized`
- `GET http://127.0.0.1:8000/sales/reports/optimized`

