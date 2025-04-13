"""empty message

Revision ID: a505eebaeae5
Revises: e62e70214231
Create Date: 2025-04-05 23:17:15.566827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a505eebaeae5'
down_revision = 'e62e70214231'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note_category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('note_category', schema=None) as batch_op:
        batch_op.drop_column('parent_id')
        batch_op.drop_column('level')

    # ### end Alembic commands ###
