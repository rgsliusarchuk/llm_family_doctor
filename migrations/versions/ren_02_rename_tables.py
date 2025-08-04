"""rename clinic → clinics, doctor → doctors, doctoranswer → doctor_answers

Revision ID: ren_02
Revises: 8e94b51d9c1d
Create Date: 2025-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "ren_02"
down_revision = "8e94b51d9c1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tables (SQLite supports RENAME TABLE directly)
    op.rename_table("clinic", "clinics")
    op.rename_table("doctor", "doctors")
    op.rename_table("doctoranswer", "doctor_answers")

    # ---- handle FK & index ----
    # Note: SQLite may not have created the constraint with the expected name
    # We'll recreate the foreign key relationship after table rename
    with op.batch_alter_table("doctors") as batch:
        # Drop any existing foreign key constraint (if it exists)
        try:
            batch.drop_constraint("fk_doctor_clinic", type_="foreignkey")
        except:
            pass  # Constraint may not exist or have different name
        
        # Drop any existing index (if it exists)
        try:
            batch.drop_index("ix_doctor_clinic_id")
        except:
            pass  # Index may not exist or have different name
        
        # Create new foreign key and index
        batch.create_foreign_key(
            "fk_doctors_clinics", "clinics", ["clinic_id"], ["id"]
        )
        batch.create_index("ix_doctors_clinic_id", ["clinic_id"])


def downgrade() -> None:
    # Reverse the operations
    with op.batch_alter_table("doctors") as batch:
        # Drop any existing foreign key constraint (if it exists)
        try:
            batch.drop_constraint("fk_doctors_clinics", type_="foreignkey")
        except:
            pass  # Constraint may not exist or have different name
        
        # Drop any existing index (if it exists)
        try:
            batch.drop_index("ix_doctors_clinic_id")
        except:
            pass  # Index may not exist or have different name
        
        # Create old foreign key and index
        batch.create_index("ix_doctor_clinic_id", ["clinic_id"])
        batch.create_foreign_key(
            "fk_doctor_clinic", "clinic", ["clinic_id"], ["id"]
        )

    op.rename_table("doctor_answers", "doctoranswer")
    op.rename_table("doctors", "doctor")
    op.rename_table("clinics", "clinic") 