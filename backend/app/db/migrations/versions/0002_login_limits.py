"""Persist owner login throttles independently of deletable guest profiles."""
from alembic import op
from app.db import LoginAttempt
revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None
def upgrade():LoginAttempt.__table__.create(op.get_bind(),checkfirst=True)
def downgrade():LoginAttempt.__table__.drop(op.get_bind(),checkfirst=True)
