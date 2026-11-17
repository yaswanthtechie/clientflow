"""add invoices and link time entries

Revision ID: 17491174a290
Revises: acf1748a331b
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "17491174a290"
down_revision: Union[str, Sequence[str], None] = "acf1748a331b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'sent', 'paid')",
            name="ck_invoices_status",
        ),
        sa.CheckConstraint(
            "total_cents >= 0",
            name="ck_invoices_total_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_invoices_id"),
        "invoices",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_invoices_client_id"),
        "invoices",
        ["client_id"],
        unique=False,
    )

    op.add_column(
        "time_entries",
        sa.Column("invoice_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_time_entries_invoice_id"),
        "time_entries",
        ["invoice_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_time_entries_invoice_id_invoices",
        "time_entries",
        "invoices",
        ["invoice_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_time_entries_invoice_id_invoices",
        "time_entries",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_time_entries_invoice_id"),
        table_name="time_entries",
    )
    op.drop_column("time_entries", "invoice_id")

    op.drop_index(op.f("ix_invoices_client_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_id"), table_name="invoices")
    op.drop_table("invoices")
