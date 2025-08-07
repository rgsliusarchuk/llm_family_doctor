"""add clinic_id to doctor

Revision ID: 8e94b51d9c1d
Revises: 799c7a3210f2
Create Date: 2025-08-04 18:42:54.855103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# NOTE: SQLite cannot ALTER TABLE to add a FK directly.
#       Batch mode copies the table, applies changes, then renames it back.


# revision identifiers, used by Alembic.
revision: str = '8e94b51d9c1d'
down_revision: Union[str, Sequence[str], None] = '799c7a3210f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("doctor") as batch:
        batch.add_column(sa.Column("clinic_id", sa.Integer(), nullable=True))
        batch.create_index("ix_doctor_clinic_id", ["clinic_id"])
        batch.create_foreign_key(
            "fk_doctor_clinic",
            "clinic",
            ["clinic_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("doctor") as batch:
        batch.drop_constraint("fk_doctor_clinic", type_="foreignkey")
        batch.drop_index("ix_doctor_clinic_id")
        batch.drop_column("clinic_id")
