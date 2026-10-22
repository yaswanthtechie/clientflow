# ClientFlow

ClientFlow is a full-stack freelancer project and invoice management application. The application helps a freelancer manage clients, projects, tasks, billable time, invoices, and dashboard reporting.

## Stack

- Frontend: React, JavaScript, Vite, React Router, Axios
- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL
- Runtime: Docker Compose

## Local development

1. Copy `.env.example` to `.env` and update local values if needed.
2. Start the application with `docker compose up --build`.
3. Open the frontend at `http://localhost:5173` and API documentation at `http://localhost:8000/docs`.

## Project documentation

- [Product requirements](docs/PRD.md)
- [Technical requirements](docs/TRD.md)
- [Application flow](docs/app-flow.md)
- [User flow](docs/user-flow.md)
- [Week 1 backlog](docs/week-1-backlog.md)

## Working agreement

- Create one branch per issue using `feature/<issue-name>`.
- Open a pull request for every issue.
- Keep `main` runnable and do not merge without passing checks.
- Friday is review day: demo completed work, explain decisions, and review tests and documentation.

## Database migrations

The backend uses SQLAlchemy and Alembic to manage database schema migrations.

1. Configure `DATABASE_URL` in `backend/.env` using the `postgresql+psycopg://` format. Never commit `.env` or expose database credentials.

2. Open a terminal in `backend` and apply pending migrations:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

3. Check the current migration revision:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic current
   ```

4. Create a migration after changing SQLAlchemy models:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic revision -m "message"
   ```

   Review the generated migration before applying it with `alembic upgrade head`.

### Database readiness

- `GET /health` checks whether the API is running.
- `GET /health/ready` checks database connectivity using `SELECT 1`.
- Readiness returns HTTP `200` with `{"status":"ready"}` when the database is available, or HTTP `503` when it is unavailable.

### Backend environment setup

1. Copy `backend/.env.example` to `backend/.env`.
2. Replace the placeholder `DATABASE_URL` with your PostgreSQL connection URL.
3. Keep `backend/.env` private; never commit real credentials.

From the `backend` directory, run migrations:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

The `/health/ready` endpoint returns `200 OK` when the database is reachable and `503 Service Unavailable` when it is unavailable.
