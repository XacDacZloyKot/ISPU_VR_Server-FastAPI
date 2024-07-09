"""Add link scenario and accident

Revision ID: c3cdf39de7f0
Revises: 
Create Date: 2024-07-09 01:12:12.131863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3cdf39de7f0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accident',
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('mechanical_accident', sa.Boolean(), nullable=True),
    sa.Column('change_value', sa.JSON(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accident'))
    )
    op.create_table('location',
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('prefab', sa.String(length=300), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_location'))
    )
    op.create_table('parameters',
    sa.Column('fields', sa.JSON(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_parameters'))
    )
    op.create_table('sensortype',
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sensortype'))
    )
    op.create_table('user',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=False),
    sa.Column('registered_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('first_name', sa.String(length=255), nullable=False),
    sa.Column('last_name', sa.String(length=255), nullable=False),
    sa.Column('patronymic', sa.String(length=50), nullable=True),
    sa.Column('is_staff', sa.Boolean(), nullable=False),
    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('division', sa.String(length=50), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user')),
    sa.UniqueConstraint('username', name=op.f('uq_user_username'))
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_table('model',
    sa.Column('specification', sa.JSON(), nullable=True),
    sa.Column('sensor_type_id', sa.Integer(), nullable=True),
    sa.Column('parameters_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['parameters_id'], ['parameters.id'], name=op.f('fk_model_parameters_id_parameters')),
    sa.ForeignKeyConstraint(['sensor_type_id'], ['sensortype.id'], name=op.f('fk_model_sensor_type_id_sensortype')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model'))
    )
    op.create_table('location_model_association',
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], name=op.f('fk_location_model_association_location_id_location')),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], name=op.f('fk_location_model_association_model_id_model'))
    )
    op.create_table('model_accident_association',
    sa.Column('model_id', sa.Integer(), nullable=True),
    sa.Column('accident_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['accident_id'], ['accident.id'], name=op.f('fk_model_accident_association_accident_id_accident')),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], name=op.f('fk_model_accident_association_model_id_model'))
    )
    op.create_table('scenario',
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('model_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], name=op.f('fk_scenario_location_id_location')),
    sa.ForeignKeyConstraint(['model_id'], ['model.id'], name=op.f('fk_scenario_model_id_model')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scenario'))
    )
    op.create_table('admission',
    sa.Column('rating', sa.String(length=4), nullable=True),
    sa.Column('status', sa.Enum('INACTIVE', 'ACTIVE', 'COMPLETED', name='admissionstatus'), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('scenario_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['scenario_id'], ['scenario.id'], name=op.f('fk_admission_scenario_id_scenario')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_admission_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_admission'))
    )
    op.create_table('scenario_accident_association',
    sa.Column('scenario_id', sa.Integer(), nullable=True),
    sa.Column('accident_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['accident_id'], ['accident.id'], name=op.f('fk_scenario_accident_association_accident_id_accident')),
    sa.ForeignKeyConstraint(['scenario_id'], ['scenario.id'], name=op.f('fk_scenario_accident_association_scenario_id_scenario'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scenario_accident_association')
    op.drop_table('admission')
    op.drop_table('scenario')
    op.drop_table('model_accident_association')
    op.drop_table('location_model_association')
    op.drop_table('model')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('sensortype')
    op.drop_table('parameters')
    op.drop_table('location')
    op.drop_table('accident')
    # ### end Alembic commands ###
