"""Add blog, user fields, chat assignment, attachments

Revision ID: a1b2c3d4e5f6
Revises: 5232b7830bf7
Create Date: 2026-07-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '5232b7830bf7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')))
        batch_op.add_column(sa.Column('is_online', sa.Boolean(), nullable=True, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('last_seen', sa.DateTime(), nullable=True))

    with op.batch_alter_table('team_member', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo_filename', sa.String(length=255), nullable=True))

    with op.batch_alter_table('chat_room', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_to_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_chat_room_assigned_to', 'user', ['assigned_to_id'], ['id'])

    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attachment_filename', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('attachment_original_name', sa.String(length=255), nullable=True))

    op.create_table(
        'blog_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=220), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )


def downgrade():
    op.drop_table('blog_post')

    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.drop_column('attachment_original_name')
        batch_op.drop_column('attachment_filename')

    with op.batch_alter_table('chat_room', schema=None) as batch_op:
        batch_op.drop_constraint('fk_chat_room_assigned_to', type_='foreignkey')
        batch_op.drop_column('assigned_to_id')

    with op.batch_alter_table('team_member', schema=None) as batch_op:
        batch_op.drop_column('photo_filename')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_seen')
        batch_op.drop_column('is_online')
        batch_op.drop_column('is_active')
