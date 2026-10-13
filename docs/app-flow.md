# Application Flow

| Screen | User action | API action | Result |
| --- | --- | --- | --- |
| Login | Submit credentials | `POST /auth/login` | Store session and open dashboard |
| Dashboard | Open summary | `GET /dashboard/summary` | Show income, projects, and invoice metrics |
| Clients | Add client | `POST /clients` | Refresh client list |
| Project | Add task or time | `POST` task or time-entry route | Update project totals |
| Invoice builder | Select unbilled time | `POST /invoices/from-time-entries` | Open draft invoice |
| Invoice details | Mark sent or paid | `PATCH /invoices/{id}/status` | Show current status |
