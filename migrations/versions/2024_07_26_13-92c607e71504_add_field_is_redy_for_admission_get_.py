"""Add field is_redy for Admission get_average_rating_for_user

Revision ID: 92c607e71504
Revises: 4f1d209636e2
Create Date: 2024-07-26 13:37:06.022436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92c607e71504'
down_revision: Union[str, None] = '4f1d209636e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('admission', sa.Column('is_ready', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('admission', 'is_ready')
    # ### end Alembic commands ###
