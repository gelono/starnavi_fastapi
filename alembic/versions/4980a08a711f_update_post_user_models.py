"""Update post/user models

Revision ID: 4980a08a711f
Revises: 0ab994418a33
Create Date: 2024-11-05 10:43:04.836056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4980a08a711f'
down_revision: Union[str, None] = '0ab994418a33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('posts', 'author_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('posts', 'author_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
