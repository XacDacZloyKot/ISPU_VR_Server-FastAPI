"""Add eng names variable

Revision ID: 8ab2810b9ee5
Revises: 145ad271de36
Create Date: 2024-09-02 21:46:18.941820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ab2810b9ee5'
down_revision: Union[str, None] = '145ad271de36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_value', sa.Column('name_eng_param', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('model_value', 'name_eng_param')
    # ### end Alembic commands ###