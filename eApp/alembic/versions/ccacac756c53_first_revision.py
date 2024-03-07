"""first revision

Revision ID: ccacac756c53
Revises: 
Create Date: 2024-02-27 08:51:09.573573

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'ccacac756c53'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def downgrade() -> None:
    # Recreate the old table with the same structure
    op.create_table('products',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('category', sa.String(30)),
            sa.Column('original_price', sa.Numeric(10, 2)),
            sa.Column('new_price', sa.Numeric(10, 2)),
            sa.Column('percentage_discount', sa.Integer),
            sa.Column('offer_expiration_date', sa.String),
            sa.Column('product_details', sa.Text, nullable=False),
            sa.Column('product_image', sa.String(200), nullable=False),
            sa.Column('is_favourite', sa.Boolean, nullable=False),
            sa.Column('add_to_cart', sa.Boolean, nullable=False),
            sa.Column('business_id', sa.Integer, sa.ForeignKey('business.id')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['business_id'], ['business.id'])
    )       

    # Copy data from the new table to the old table, explicitly specifying columns
    op.execute('INSERT INTO products (id, name, category, original_price, new_price, percentage_discount, offer_expiration_date, product_details, product_image, is_favourite, add_to_cart, business_id) SELECT id, name, category, original_price, new_price, percentage_discount, offer_expiration_date, product_details, product_image, is_favourite, add_to_cart, business_id FROM upTwo')

    # Drop the new table
    op.drop_table('upTwo')
