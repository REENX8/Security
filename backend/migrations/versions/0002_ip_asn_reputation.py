"""ip/asn reputation tables (B8)

Revision ID: 0002_ip_asn_reputation
Revises: 0001_baseline
Create Date: 2026-06-05

Adds the ``ip_reputation`` and ``asn_reputation`` tables. The baseline
(0001) builds the schema from live ``Base.metadata`` via ``create_all``, so on a
FRESH database these tables already exist by the time this revision runs — the
``checkfirst=True`` creates below are therefore no-ops there. On an EXISTING
database that stopped at 0001, this revision creates the two new tables. This
keeps ``alembic upgrade head`` consistent with ``app/models.py`` in both cases.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.models import AsnReputation, IpReputation

# revision identifiers, used by Alembic.
revision: str = "0002_ip_asn_reputation"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    IpReputation.__table__.create(bind=bind, checkfirst=True)
    AsnReputation.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    AsnReputation.__table__.drop(bind=bind, checkfirst=True)
    IpReputation.__table__.drop(bind=bind, checkfirst=True)
