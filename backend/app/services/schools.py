"""School slug + find-or-create helpers (shared by the schools router and sign-up)."""
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:60] or "school"


async def find_or_create_school(db: AsyncSession, name: str, **fields) -> School:
    """Return the existing school for this name's slug, or create it. Idempotent.

    The caller is responsible for the surrounding transaction/commit.
    """
    slug = slugify(name)
    existing = await db.scalar(select(School).where(School.slug == slug))
    if existing is not None:
        return existing
    school = School(slug=slug, name=name, **fields)
    db.add(school)
    try:
        await db.flush()
    except IntegrityError:  # raced insert on same slug
        await db.rollback()
        school = await db.scalar(select(School).where(School.slug == slug))
        assert school is not None
    return school
