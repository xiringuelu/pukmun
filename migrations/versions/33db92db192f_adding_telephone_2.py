"""adding telephone 2

Revision ID: 33db92db192f
Revises: 66d39d3c9ac4
Create Date: 2020-11-10 15:57:44.990078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33db92db192f'
down_revision = '66d39d3c9ac4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('telephones', sa.Column('number2', sa.String(length=15), nullable=True))
    op.add_column('telephones', sa.Column('user_id', sa.Integer(), nullable=True))
    op.drop_constraint(None, 'telephones', type_='foreignkey')
    op.create_foreign_key(None, 'telephones', 'user', ['user_id'], ['id'])
    op.drop_column('telephones', 'race_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('telephones', sa.Column('race_id', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'telephones', type_='foreignkey')
    op.create_foreign_key(None, 'telephones', 'user', ['race_id'], ['id'])
    op.drop_column('telephones', 'user_id')
    op.drop_column('telephones', 'number2')
    # ### end Alembic commands ###
