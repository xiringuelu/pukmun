"""adding notifications

Revision ID: 1359f424b8dc
Revises: 4f6e0cb0c92a
Create Date: 2020-11-28 11:08:35.454056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1359f424b8dc'
down_revision = '4f6e0cb0c92a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('content', sa.String(length=2500), nullable=False),
    sa.Column('seen', sa.Boolean(), nullable=True),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notification_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notification_timestamp'))

    op.drop_table('notification')
    # ### end Alembic commands ###
