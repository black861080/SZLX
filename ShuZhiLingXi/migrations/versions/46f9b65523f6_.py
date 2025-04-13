"""empty message

Revision ID: 46f9b65523f6
Revises: 26522fffac47
Create Date: 2025-02-19 15:34:21.618944

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '46f9b65523f6'
down_revision = '26522fffac47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notes_chapter', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=50),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notes_chapter', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.String(length=50),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)
        batch_op.drop_column('category')

    # ### end Alembic commands ###
