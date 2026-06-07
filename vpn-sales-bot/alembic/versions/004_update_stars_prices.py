"""update stars prices

Revision ID: 004
Revises: 003
Create Date: 2026-06-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STARS_BY_CODE = {
    "month_1": 150,
    "month_3": 400,
    "year_1": 1000,
}


def upgrade() -> None:
    connection = op.get_bind()
    for code, stars in STARS_BY_CODE.items():
        connection.execute(
            sa.text("UPDATE plans SET stars_price = :stars WHERE code = :code"),
            {"stars": stars, "code": code},
        )


def downgrade() -> None:
    old_prices = {
        "month_1": 50,
        "month_3": 120,
        "year_1": 350,
    }
    connection = op.get_bind()
    for code, stars in old_prices.items():
        connection.execute(
            sa.text("UPDATE plans SET stars_price = :stars WHERE code = :code"),
            {"stars": stars, "code": code},
        )
