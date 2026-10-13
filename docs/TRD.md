# Technical Requirements Document

## Architecture

React JavaScript frontend calls a FastAPI REST API through Axios. FastAPI validates requests, enforces JWT-based ownership, applies business rules, and persists data in PostgreSQL through SQLAlchemy.

## Stack

- React, JavaScript, Vite, Axios, React Router
- FastAPI, Pydantic, SQLAlchemy, Alembic
- PostgreSQL
- Docker Compose

## Technical rules

- All protected resources must be owned by the authenticated user.
- React must use one shared API client for base URL, token attachment, and error handling.
- Backend services calculate invoice totals; frontend values are never the source of truth.
- CORS permits only the frontend development or deployed origin.
- Schema changes use Alembic migrations.

## Initial API contract

- `GET /health` returns application status.
- Future routes live under `auth`, `clients`, `projects`, `tasks`, `time-entries`, `invoices`, and `dashboard` routers.
