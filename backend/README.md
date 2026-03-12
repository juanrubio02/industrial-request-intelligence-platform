# Industrial Request Intelligence Platform Backend

Base backend scaffold with a modular architecture ready to grow into a SaaS industrial platform.

## Quickstart

From the project root:

```bash
./scripts/bootstrap_local.sh
```

That flow:

- starts backend, PostgreSQL and Redis with Docker Compose,
- creates `frontend/.env.local`,
- applies Alembic migrations inside the backend container,
- seeds a demo organization, user and membership.

Demo login after bootstrapping:

```text
email: admin@acme.com
password: Admin1234
```

## Run locally without bootstrap

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.local.example .env
alembic upgrade head
python scripts/seed_demo.py
uvicorn app.main:app --host 127.0.0.1 --port 28000 --reload
```

## Run tests

```bash
pytest
```
