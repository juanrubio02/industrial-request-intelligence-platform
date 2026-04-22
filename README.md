# ForgeFlow Business Request Management Platform

Fullstack request operations system for managing ForgeFlow RFQs, attached documents, workflow status, ownership, comments, and reviewed document data.

## Key Highlights

- End-to-end business request workflow: intake, assignment, status tracking, comments, timeline, document review, and verified data.
- Built as a real product surface, not a generic CRM: the workflow is centered on ForgeFlow quoting and document-heavy commercial requests.
- Document processing is visible inside the operator workflow: uploaded files are processed, summarized, classified, and reviewed before data is trusted.
- Multi-tenant backend foundation with authenticated users, organization membership context, role-aware access, and tenant-scoped APIs.
- Local demo runs without external SaaS dependencies using Docker Compose, seeded data, PostgreSQL, Redis, FastAPI, and Next.js.

## What the System Does

ForgeFlow teams often receive RFQs, specifications, purchase documents, and follow-up details across fragmented channels. This platform turns that intake into a structured operational queue where each request has ownership, status, documents, comments, extracted information, and a review trail.

The result is a focused business request management system for teams that need to move document-heavy opportunities from incoming demand to reviewed operational context.

## Core Features

- Organization-scoped workspace with demo authentication
- Request list and request detail views
- Request creation through guided demo intake scenarios
- Status progression for ForgeFlow request workflows
- Assignment and internal collaboration comments
- Activity timeline tied to each request
- Document upload and processing status tracking
- Text extraction, document type detection, and summary generation
- Human-reviewed structured fields before data is treated as verified
- Demo seed data and realistic RFQ scenarios for evaluation

## Architecture

```text
frontend/   Next.js product UI for login, request operations, document review, and demo intake
backend/    FastAPI service with domain, application, infrastructure, and HTTP layers
scripts/    Local development helpers for startup, checks, logs, and shutdown
```

High-level flow:

1. A user signs in and works inside an organization membership context.
2. Requests are created manually or generated through demo intake scenarios.
3. Documents are attached to requests and stored locally.
4. The backend processes documents for text, type, summary, and structured fields.
5. An operator reviews request status, ownership, comments, timeline, and verified document data.

Backend boundaries:

- `domain`: core entities, enums, and business rules
- `application`: use cases, commands, read models, and authorization policies
- `infrastructure`: database repositories, JWT, storage, and document processing adapters
- `interfaces/http`: FastAPI routes, middleware, dependency injection, and API schemas

## Tech Stack

**Frontend**

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- TanStack Query
- Vitest

**Backend**

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- pytest

**Document Processing**

- Local file storage
- PDF parsing
- OCR fallback
- Deterministic text summary and structured field extraction
- Human verification workflow

**Local Development**

- Docker Compose
- Seed scripts
- Health and flow check scripts

## Demo / How to Run

Requirements:

- Docker + Docker Compose
- Node.js 20+ with `npm`
- Python 3 available in `PATH`

Start the full application:

```bash
./scripts/dev-up.sh
./scripts/dev-check.sh
```

Open the frontend:

```text
http://localhost:3000/login
```

Demo credentials:

```text
Email: admin@acme.com
Password: Admin1234
```

Useful commands:

```bash
./scripts/dev-up.sh --rebuild
./scripts/dev-down.sh
./scripts/dev-logs.sh
./scripts/dev-check.sh --deep
```

Default local ports:

- Frontend: `3000`
- Backend API: `8000`
- Test PostgreSQL: `55433`
- PostgreSQL container: `5432`
- Redis container: `6379`

## Suggested Demo Flow

1. Log in with the seeded demo account.
2. Open the guided demo.
3. Run the `RFQ - Stainless Steel Mounting Brackets` scenario.
4. Review the generated request detail page.
5. Show assignment, comments, timeline, and status.
6. Open the attached document.
7. Review extracted text, summary, document type, and verified fields.

## Screenshots

Screenshots can be added here for:

- Request queue
- Request detail
- Document processing result
- Verified structured data

## Validation

Frontend:

```bash
cd frontend
npm test
npm run build
```

Backend:

```bash
docker compose up -d postgres_test
cd backend
source .venv/bin/activate
pytest
```

## Current Scope

- Authentication is demo-grade and designed for local evaluation.
- File storage is local filesystem storage.
- Document processing is deterministic and local, suitable for portfolio demonstration.
- Background worker deployment and production object storage are outside the current scope.
