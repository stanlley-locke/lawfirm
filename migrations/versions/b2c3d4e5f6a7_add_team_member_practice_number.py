"""Add practice_number to team_member

Revision ID: b2c3d4e5f6a7
Revises: a54586e1e775
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = '18d943de40ed'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('team_member', schema=None) as batch_op:
        batch_op.add_column(sa.Column('practice_number', sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table('team_member', schema=None) as batch_op:
        batch_op.drop_column('practice_number')
