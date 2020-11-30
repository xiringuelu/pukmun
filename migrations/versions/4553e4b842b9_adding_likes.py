"""adding likes

Revision ID: 4553e4b842b9
Revises: 11d9a35a8cd0
Create Date: 2020-11-25 17:14:11.271740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4553e4b842b9'
down_revision = '11d9a35a8cd0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe_like', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recipe_id', sa.Integer(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'recipe', ['recipe_id'], ['id'])
        batch_op.drop_column('post_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe_like', schema=None) as batch_op:
        batch_op.add_column(sa.Column('post_id', sa.INTEGER(), nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'recipe', ['post_id'], ['id'])
        batch_op.drop_column('recipe_id')

    # ### end Alembic commands ###
