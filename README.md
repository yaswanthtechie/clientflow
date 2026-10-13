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
