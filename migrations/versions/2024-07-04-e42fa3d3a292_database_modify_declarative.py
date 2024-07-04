"""Database Modify Declarative

Revision ID: e42fa3d3a292
Revises: 52fbd8a3ce96
Create Date: 2024-07-04 22:47:52.651356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'e42fa3d3a292'
down_revision: Union[str, None] = '52fbd8a3ce96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('hashed_password', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('email', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('username', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('registered_at', mysql.TIMESTAMP(), nullable=True),
    sa.Column('first_name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('last_name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('is_staff', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('role_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('is_superuser', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('is_verified', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='user_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
