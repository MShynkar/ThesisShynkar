"""Denormalize access_level onto chunks (enables HNSW-indexed RBAC search)

Revision ID: 0002_chunk_access_level
Revises: 0001_initial
Create Date: 2026-05-29 00:00:00.000000

The semantic/hybrid search filters by access_level. While that column lived only
on `documents`, the query had to JOIN documents and filter there, which prevented
the PostgreSQL planner from using the HNSW index on chunks.embedding (it fell back
to an exact brute-force sort). Copying access_level onto `chunks` lets the filter
sit on the same table as the vector ORDER BY, so the HNSW index can be used.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_chunk_access_level"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chunks", sa.Column("access_level", sa.String(20), nullable=True))
    # Backfill from the parent document
    op.execute(
        "UPDATE chunks c SET access_level = d.access_level "
        "FROM documents d WHERE c.document_id = d.id"
    )
    # Safety net for any orphan/edge row
    op.execute("UPDATE chunks SET access_level = 'internal' WHERE access_level IS NULL")
    op.alter_column("chunks", "access_level", nullable=False, server_default="internal")
    op.create_index("ix_chunks_access_level", "chunks", ["access_level"])


def downgrade() -> None:
    op.drop_index("ix_chunks_access_level", table_name="chunks")
    op.drop_column("chunks", "access_level")
