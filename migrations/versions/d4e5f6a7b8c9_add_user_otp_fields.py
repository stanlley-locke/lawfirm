"""Add OTP two-factor login fields to user

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('otp_code_hash', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('otp_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('otp_attempts', sa.Integer(), nullable=True, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('otp_last_sent_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('otp_last_sent_at')
        batch_op.drop_column('otp_attempts')
        batch_op.drop_column('otp_expires_at')
        batch_op.drop_column('otp_code_hash')
