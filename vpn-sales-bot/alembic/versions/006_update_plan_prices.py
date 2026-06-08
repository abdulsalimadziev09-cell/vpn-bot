"""update stars prices and deactivate year plan

Revision ID: 006
Revises: 005
Create Date: 2026-06-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STARS_BY_CODE = {
    "month_1": 100,
    "month_3": 250,
}


def upgrade() -> None:
    for code, stars in STARS_BY_CODE.items():
        op.execute(
            sa.text("UPDATE plans SET stars_price = :stars WHERE code = :code"),
            {"stars": stars, "code": code},
        )
    op.execute(sa.text("UPDATE plans SET is_active = false WHERE code = 'year_1'"))


def downgrade() -> None:
    old_prices = {
        "month_1": 150,
        "month_3": 400,
    }
    for code, stars in old_prices.items():
        op.execute(
            sa.text("UPDATE plans SET stars_price = :stars WHERE code = :code"),
            {"stars": stars, "code": code},
        )
    op.execute(sa.text("UPDATE plans SET is_active = true WHERE code = 'year_1'"))
