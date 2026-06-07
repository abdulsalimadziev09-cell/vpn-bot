"""add stars_price to plans

Revision ID: 002
Revises: 001
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STARS_BY_CODE = {
    "month_1": 50,
    "month_3": 120,
    "year_1": 350,
}


def upgrade() -> None:
    op.add_column(
        "plans",
        sa.Column("stars_price", sa.Integer(), nullable=False, server_default="50"),
    )
    connection = op.get_bind()
    for code, stars in STARS_BY_CODE.items():
        connection.execute(
            sa.text("UPDATE plans SET stars_price = :stars WHERE code = :code"),
            {"stars": stars, "code": code},
        )


def downgrade() -> None:
    op.drop_column("plans", "stars_price")
