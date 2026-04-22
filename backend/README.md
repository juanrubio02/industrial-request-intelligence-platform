# Backend

Backend service for the ForgeFlow.

The official development workflow lives in the root [`README.md`](../README.md) and starts from [`scripts/dev-up.sh`](../scripts/dev-up.sh).

## Official workflow

```bash
cd ..
./scripts/dev-up.sh
./scripts/dev-check.sh
```

That flow keeps the development ports fixed:

- frontend: `3000`
- backend: `8000`
- postgres test: `55433`

## Optional backend-only local run

Use this only if you intentionally want to run FastAPI outside Docker and you already have PostgreSQL and Redis reachable on `localhost`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.local.example .env
alembic upgrade head
python scripts/seed_demo.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Tests

```bash
docker compose up -d postgres_test
cd backend
source .venv/bin/activate
pytest
```
