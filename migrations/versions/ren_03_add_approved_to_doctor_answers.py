"""add 'approved' column to doctor_answers

Revision ID: ren_03
Revises: ren_02
Create Date: 2025-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "ren_03"
down_revision = "ren_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("doctor_answers") as batch:
        batch.add_column(sa.Column("approved", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("doctor_answers") as batch:
        batch.drop_column("approved") 