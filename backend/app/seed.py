"""
Seed script — populates the database with demo users and a few sample documents.

Run from inside the backend container:
    python -m app.seed
"""
import asyncio
import os
from pathlib import Path

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.permissions import AccessLevel, Role
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.document import Document
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.document_service import DocumentService

configure_logging()
logger = get_logger(__name__)


DEMO_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin123!",
        "full_name": "System Administrator",
        "role": Role.ADMIN,
    },
    {
        "email": "manager@example.com",
        "username": "manager",
        "password": "manager123!",
        "full_name": "Demo Manager",
        "role": Role.MANAGER,
    },
    {
        "email": "user@example.com",
        "username": "user",
        "password": "user123!",
        "full_name": "Regular User",
        "role": Role.USER,
    },
    {
        "email": "guest@example.com",
        "username": "guest",
        "password": "guest123!",
        "full_name": "Guest User",
        "role": Role.GUEST,
    },
]

SAMPLE_DOCS = [
    {
        "title": "Company Handbook",
        "filename": "handbook.txt",
        "access_level": AccessLevel.PUBLIC,
        "category": "HR",
        "tags": ["handbook", "policy"],
        "content": (
            "Welcome to the company handbook. Our mission is to build trustworthy AI tools.\n\n"
            "Working hours are flexible: most teams work 9am to 6pm in their local timezone. "
            "We support remote work and encourage asynchronous communication.\n\n"
            "Time off: every employee gets 25 days of paid vacation per year, "
            "plus public holidays. Sick leave is unlimited and based on trust.\n\n"
            "Code of conduct: be respectful, be honest, and prioritize user safety. "
            "Discrimination or harassment of any kind is grounds for immediate termination."
        ),
    },
    {
        "title": "Engineering Best Practices",
        "filename": "engineering.md",
        "access_level": AccessLevel.INTERNAL,
        "category": "Engineering",
        "tags": ["engineering", "practices"],
        "content": (
            "# Engineering Best Practices\n\n"
            "## Code Review\n"
            "Every change requires at least one approval from a peer. "
            "Reviews should focus on correctness, security, and maintainability.\n\n"
            "## Testing\n"
            "All new features must have unit tests. Integration tests are required for API endpoints. "
            "Target test coverage is 80% or higher.\n\n"
            "## Deployment\n"
            "We deploy continuously from main. All deployments are blue/green and can be rolled back "
            "within 60 seconds via the rollback dashboard.\n\n"
            "## Security\n"
            "Never commit secrets. Use the vault for credentials. "
            "Rotate API keys every 90 days. Run dependency scans weekly."
        ),
    },
    {
        "title": "Q4 Strategic Plan",
        "filename": "q4_plan.txt",
        "access_level": AccessLevel.CONFIDENTIAL,
        "category": "Strategy",
        "tags": ["strategy", "planning", "q4"],
        "content": (
            "Q4 Strategic Priorities (CONFIDENTIAL — managers and above only)\n\n"
            "1. Launch the new RAG platform with enterprise SSO and SOC2 compliance. "
            "Target GA date: end of Q4. Revenue target: $2M ARR by year end.\n\n"
            "2. Expand the engineering team by 12 senior hires, focusing on infra and security. "
            "Headcount budget: approved.\n\n"
            "3. Acquire competitor SmallCo for an estimated $15M. "
            "Due diligence is underway. Target close: November 30.\n\n"
            "4. Maintain gross margin above 70%. "
            "Cost-of-goods optimization is led by the platform team."
        ),
    },
    {
        "title": "Executive Compensation Review",
        "filename": "exec_comp.txt",
        "access_level": AccessLevel.RESTRICTED,
        "category": "HR",
        "tags": ["compensation", "executive"],
        "content": (
            "Executive Compensation Review — Q4 (RESTRICTED — admin only)\n\n"
            "CEO base salary: $450,000 with a target bonus of 100% of base, "
            "plus equity grant of 50,000 RSUs vesting over 4 years.\n\n"
            "CTO base salary: $400,000 with a target bonus of 80% of base, "
            "plus equity grant of 40,000 RSUs.\n\n"
            "CFO base salary: $380,000. The board approved an additional retention grant "
            "of 20,000 RSUs subject to a 3-year cliff.\n\n"
            "All packages benchmarked against the 75th percentile of comparable companies in our region."
        ),
    },
]


async def seed_users() -> dict[str, User]:
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        created: dict[str, User] = {}
        for u in DEMO_USERS:
            existing = await repo.get_by_email(u["email"])
            if existing:
                logger.info("user_exists", email=u["email"])
                created[u["role"].value] = existing
                continue
            user = User(
                email=u["email"],
                username=u["username"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"].value,
                is_active=True,
            )
            await repo.create(user)
            created[u["role"].value] = user
            logger.info("user_created", email=u["email"], role=u["role"].value)
        await session.commit()
        return created


async def seed_documents(users: dict[str, User]) -> None:
    """Write sample text files to disk and create document rows pointing at them.

    We bypass the upload endpoint here; instead we write content directly,
    then run the same processing pipeline.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    admin = users.get(Role.ADMIN.value)
    if not admin:
        logger.error("seed_no_admin")
        return

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        existing = (
            await session.execute(select(Document).where(Document.title.in_([d["title"] for d in SAMPLE_DOCS])))
        ).scalars().all()
        existing_titles = {d.title for d in existing}

        docs_to_process: list[Document] = []
        for spec in SAMPLE_DOCS:
            if spec["title"] in existing_titles:
                logger.info("doc_exists", title=spec["title"])
                continue
            ext = Path(spec["filename"]).suffix.lower().lstrip(".")
            stored_name = f"seed_{spec['title'].lower().replace(' ', '_')}.{ext}"
            stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
            Path(stored_path).write_text(spec["content"], encoding="utf-8")

            doc = Document(
                title=spec["title"],
                filename=spec["filename"],
                file_path=stored_path,
                file_size=len(spec["content"].encode("utf-8")),
                mime_type="text/plain" if ext == "txt" else "text/markdown",
                owner_id=admin.id,
                access_level=spec["access_level"].value,
                category=spec["category"],
                tags=spec["tags"],
                doc_metadata={"source": "seed"},
                status="pending",
            )
            session.add(doc)
            docs_to_process.append(doc)
        await session.commit()
        for d in docs_to_process:
            await session.refresh(d)
        doc_ids = [d.id for d in docs_to_process]

    # Process each one with its own session so we don't hold a session during HTTP calls
    for doc_id in doc_ids:
        async with AsyncSessionLocal() as session:
            service = DocumentService(session)
            try:
                await service.process(doc_id)
                logger.info("seed_doc_processed", doc_id=str(doc_id))
            except Exception as e:
                logger.exception("seed_doc_failed", doc_id=str(doc_id), error=str(e))


async def main():
    logger.info("seed_starting")
    users = await seed_users()
    try:
        await seed_documents(users)
    except Exception:
        logger.exception("seed_documents_failed_but_users_created")
        logger.info("you_can_still_login_with_demo_users")
    logger.info("seed_complete")


if __name__ == "__main__":
    asyncio.run(main())
