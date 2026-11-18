from pydantic import BaseModel


class InvoiceTotals(BaseModel):
    unpaid_cents: int
    paid_cents: int


class DashboardResponse(BaseModel):
    total_clients: int
    active_projects: int
    billable_hours_this_month: float
    invoice_totals: InvoiceTotals
