"""empty message

Revision ID: 4c759d4bbd9d
Revises: d79d36dbd099
Create Date: 2025-02-20 11:21:58.703313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c759d4bbd9d'
down_revision = 'd79d36dbd099'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('plan',
    sa.Column('plan_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('todo', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('level', sa.Enum('紧急', '非紧急'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('plan_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('plan')
    # ### end Alembic commands ###
