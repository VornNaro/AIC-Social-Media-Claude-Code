"""Seed the database with SchoolMate demo content.

Run inside the backend container:
    docker compose run --rm backend python scripts/seed.py

Idempotent: if the demo school already exists it does nothing. Asset paths point
at files served by the frontend from /public/schoolmate/*.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.connection import Connection, ConnectionStatus
from app.models.post import Post
from app.models.reunion import Reunion, Rsvp, RsvpStatus
from app.models.school import School, SchoolMembership
from app.models.user import User

A = "/schoolmate/people/"
PH = "/schoolmate/photos/"
PW = "password123"  # demo password for every seeded account

PEOPLE = [
    # username,    display,           year, city,        avatar,        role
    ("aisha",  "Aisha Sharma",   2012, "Pune",      "aisha.png", "Photographer & founder, Studio Marigold"),
    ("rohan",  "Rohan Mehta",    2011, "Mumbai",    "rohan.png", "Cricket coach"),
    ("arjun",  "Arjun Kapoor",   2013, "Bengaluru", "arjun.png", "Product designer"),
    ("neha",   "Neha Iyer",      2009, "Chennai",   "neha.png",  "Schoolteacher"),
    ("priya",  "Priya Nair",     2012, "Kochi",     "p3.png",    "Pediatrician"),
    ("vikram", "Vikram Desai",   2012, "Ahmedabad", "p2.png",    "Civil engineer"),
    ("meera",  "Meera Krishnan", 2011, "Hyderabad", "p4.png",    "Chef & cafe owner"),
    ("karan",  "Karan Malhotra", 2012, "Jaipur",    "p1.png",    "Architect"),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        if await db.scalar(select(School).where(School.slug == "chungbuk-national-university")):
            print("Demo data already present — skipping.")
            return

        now = datetime.now(timezone.utc)

        school = School(
            slug="chungbuk-national-university",
            name="Chungbuk National University",
            short_name="CBNU",
            location="Cheongju, South Korea",
            founded=1951,
            cover_url=PH + "cbnu-campus.jpg",
            motto="Where every story begins.",
        )
        db.add(school)
        await db.flush()

        users: dict[str, User] = {}
        for uname, display, year, city, avatar, role in PEOPLE:
            u = User(
                username=uname,
                email=f"{uname}@schoolmate.demo",
                hashed_password=hash_password(PW),
                display_name=display,
                graduation_year=year,
                city=city,
                role=role,
                avatar_url=A + avatar,
                school_id=school.id,
                interests=["Photography", "Road trips", "Filter coffee"] if uname == "aisha" else [],
                bio=f"CBNU, Class of {year}." ,
            )
            db.add(u)
            users[uname] = u
        await db.flush()

        # everyone joins the school community
        for u in users.values():
            db.add(SchoolMembership(school_id=school.id, user_id=u.id))

        aisha = users["aisha"]
        aisha.cover_url = PH + "cbnu-campus.jpg"
        aisha.bio = (
            "CBNU kid, Class of 2012. I run a little photography studio in Cheongju and "
            "still keep every roll of film from our campus trips. ♥"
        )

        posts = [
            Post(
                author_id=users["rohan"].id,
                content="Throwback to our inter-college sports day — that championship still "
                "feels like yesterday. Those were the days. 🏆",
                image_url=PH + "sportevent.png",
                tags=["#SchoolDays", "#SportsDay"],
                created_at=now - timedelta(hours=2),
            ),
            Post(
                author_id=users["neha"].id,
                content="Campus picnic with the old gang last weekend. Grateful for the friends "
                "who turned into family. ☕",
                image_url=PH + "picnic.png",
                tags=["#SomeBondsNeverFade"],
                note="Some bonds never fade.",
                created_at=now - timedelta(hours=4),
            ),
            Post(
                author_id=aisha.id,
                content="Graduation day — caps in the air and not a dry eye in sight. Hard to "
                "believe it's been over a decade. Tag your favorite grad! 🎓",
                image_url=PH + "graduation.jpg",
                tags=["#GraduationDay", "#ClassOf2012"],
                created_at=now - timedelta(days=1),
            ),
        ]
        db.add_all(posts)

        reunion = Reunion(
            school_id=school.id,
            host_id=users["rohan"].id,
            title="15-Year Reunion",
            class_year=2011,
            starts_at=datetime(2026, 8, 15, 18, 0, tzinfo=timezone.utc),
            ends_at=datetime(2026, 8, 15, 22, 0, tzinfo=timezone.utc),
            venue="The Grand Lawn",
            address="The Grand Lawn, Cheongju",
            city="Cheongju",
            cover_url=PH + "picnic.png",
            description=(
                "Fifteen years on, the Class of 2011 is getting the band back together. An "
                "evening of dinner, dancing, a yearbook slideshow, and far too many "
                '"remember when" stories.'
            ),
            amenities=["Dinner included", "Yearbook slideshow", "Live band", "Family friendly"],
        )
        mixer = Reunion(
            school_id=school.id,
            host_id=aisha.id,
            title="Summer Mixer",
            class_year=2012,
            starts_at=datetime(2026, 7, 18, 17, 0, tzinfo=timezone.utc),
            ends_at=datetime(2026, 7, 18, 21, 0, tzinfo=timezone.utc),
            venue="Riverside Cafe",
            address="Riverside Cafe, Cheongju",
            city="Cheongju",
            cover_url=PH + "cbnu-campus.jpg",
            description="A relaxed evening catch-up for the Class of 2012. Good food, old friends, no agenda.",
            amenities=["Coffee & cake", "Open mic"],
        )
        db.add_all([reunion, mixer])
        await db.flush()

        going = ["rohan", "neha", "arjun", "priya", "meera", "karan"]
        for uname in going:
            db.add(Rsvp(reunion_id=reunion.id, user_id=users[uname].id, status=RsvpStatus.GOING))
        db.add(Rsvp(reunion_id=reunion.id, user_id=users["vikram"].id, status=RsvpStatus.MAYBE))
        for uname in ["priya", "vikram", "karan"]:
            db.add(Rsvp(reunion_id=mixer.id, user_id=users[uname].id, status=RsvpStatus.GOING))

        # aisha is connected to a few classmates; arjun/priya are pending
        for uname in ["rohan", "neha", "meera", "karan"]:
            db.add(Connection(
                requester_id=aisha.id, addressee_id=users[uname].id,
                status=ConnectionStatus.ACCEPTED,
            ))
        db.add(Connection(
            requester_id=users["arjun"].id, addressee_id=aisha.id,
            status=ConnectionStatus.PENDING,
        ))

        await db.commit()
        print(
            f"Seeded: 1 school, {len(users)} users (password '{PW}'), "
            f"{len(posts)} posts, 2 reunions, connections. Log in as aisha@schoolmate.demo."
        )


if __name__ == "__main__":
    asyncio.run(seed())
