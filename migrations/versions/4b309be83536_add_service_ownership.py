"""add service ownership

Revision ID: 4b309be83536
Revises: 25fa2b60d69d
Create Date: 2026-08-08 16:05:21.337177

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b309be83536"
down_revision: Union[str, Sequence[str], None] = "25fa2b60d69d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("owner_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            "ix_services_owner_id",
            ["owner_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_services_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_services_owner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_services_owner_id")
        batch_op.drop_column("owner_id")
