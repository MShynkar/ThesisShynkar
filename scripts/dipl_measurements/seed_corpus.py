"""Point 1: load the expanded measurement corpus into the database.

Writes each document to the uploads dir and runs the SAME processing pipeline
the application uses (DocumentService.process -> extract -> chunk -> embed via
Ollama -> persist + tsvector). Documents are tagged doc_metadata.source =
'dipl_seed' so they can be identified and, if ever needed, removed.

Existing documents (matched by title) are skipped, so this is idempotent and
keeps the original 5 demo documents intact.

Run:
    cd backend
    ./.venv/Scripts/python.exe ../scripts/dipl_measurements/seed_corpus.py
"""
import asyncio
import os
import time
from pathlib import Path

import _common  # noqa: F401
from corpus_data import documents
from sqlalchemy import select

from app.core.config import settings
from app.core.permissions import Role
from app.db.session import AsyncSessionLocal
from app.models.document import Document
from app.models.user import User
from app.services.document_service import DocumentService


async def get_admin() -> User:
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(select(User).where(User.role == Role.ADMIN.value))
        ).scalars().first()
        if not admin:
            raise SystemExit("No admin user found — run `python -m app.seed` first.")
        return admin


async def main() -> None:
    admin = await get_admin()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    docs = documents()

    # Create rows for documents that don't already exist.
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(
                select(Document.title).where(Document.title.in_([d["title"] for d in docs]))
            )
        ).scalars().all()
        existing_titles = set(existing)

        to_process: list = []
        for spec in docs:
            if spec["title"] in existing_titles:
                print(f"  skip (exists): {spec['title']}")
                continue
            stored_name = f"dipl_{spec['title'].lower().replace(' ', '_').replace('/', '_')}.txt"
            stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
            Path(stored_path).write_text(spec["content"], encoding="utf-8")
            doc = Document(
                title=spec["title"],
                filename=stored_name,
                file_path=stored_path,
                file_size=len(spec["content"].encode("utf-8")),
                mime_type="text/plain",
                owner_id=admin.id,
                access_level=spec["access_level"],
                category=spec["category"],
                tags=spec["tags"],
                doc_metadata={"source": "dipl_seed"},
                status="pending",
            )
            session.add(doc)
            to_process.append(doc)
        await session.commit()
        for d in to_process:
            await session.refresh(d)
        doc_ids = [(d.id, d.title) for d in to_process]

    print(f"\nProcessing {len(doc_ids)} new documents (chunk + embed) ...")
    t0 = time.perf_counter()
    for doc_id, title in doc_ids:
        async with AsyncSessionLocal() as session:
            service = DocumentService(session)
            ts = time.perf_counter()
            await service.process(doc_id)
            print(f"  [{(time.perf_counter()-ts):6.1f}s] {title}")
    print(f"Done in {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
