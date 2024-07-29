"""Delete model parameters

Revision ID: 22a5f4d19678
Revises: 92c607e71504
Create Date: 2024-07-28 17:58:46.233693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '22a5f4d19678'
down_revision: Union[str, None] = '92c607e71504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем внешний ключ
    op.drop_constraint('fk_model_parameters_id_parameters', 'model', type_='foreignkey')

    # Удаляем колонку
    op.drop_column('model', 'parameters_id')

    # Удаляем таблицу
    op.drop_table('parameters')


def downgrade() -> None:
    # Восстанавливаем таблицу
    op.create_table('parameters',
        sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('fields', mysql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    # Восстанавливаем колонку в таблице 'model'
    op.add_column('model', sa.Column('parameters_id', mysql.INTEGER(), autoincrement=False, nullable=True))

    # Восстанавливаем внешний ключ
    op.create_foreign_key('fk_model_parameters_id_parameters', 'model', 'parameters', ['parameters_id'], ['id'])
