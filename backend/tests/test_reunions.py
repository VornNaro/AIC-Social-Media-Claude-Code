import uuid

from tests.conftest import auth_header


async def _school_and_reunion(client, user):
    slug = (
        await client.post(
            "/api/v1/schools", json={"name": "CBNU"}, headers=auth_header(user)
        )
    ).json()["slug"]
    r = await client.post(
        f"/api/v1/schools/{slug}/reunions",
        json={
            "title": "15-Year Reunion",
            "class_year": 2011,
            "starts_at": "2026-08-15T18:00:00Z",
            "venue": "The Grand Lawn",
            "city": "Cheongju",
            "amenities": ["Dinner included", "Live band"],
        },
        headers=auth_header(user),
    )
    return slug, r


async def test_create_reunion_host_auto_going(client, user):
    _, r = await _school_and_reunion(client, user)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "15-Year Reunion"
    assert data["host"]["username"] == "alice"
    assert data["going_count"] == 1  # host auto-RSVPs
    assert data["my_rsvp"] == "GOING"


async def test_rsvp_going_then_maybe_then_clear(client, user, second_user):
    _, r = await _school_and_reunion(client, user)
    rid = r.json()["id"]
    h = auth_header(second_user)

    going = (
        await client.put(f"/api/v1/reunions/{rid}/rsvp", json={"status": "GOING"}, headers=h)
    ).json()
    assert going["going_count"] == 2
    assert going["my_rsvp"] == "GOING"

    maybe = (
        await client.put(f"/api/v1/reunions/{rid}/rsvp", json={"status": "MAYBE"}, headers=h)
    ).json()
    assert maybe["going_count"] == 1  # no longer counted as going
    assert maybe["my_rsvp"] == "MAYBE"

    cleared = (await client.delete(f"/api/v1/reunions/{rid}/rsvp", headers=h)).json()
    assert cleared["my_rsvp"] is None
    assert cleared["going_count"] == 1


async def test_attendees_excludes_declined(client, user, second_user):
    _, r = await _school_and_reunion(client, user)
    rid = r.json()["id"]
    await client.put(
        f"/api/v1/reunions/{rid}/rsvp", json={"status": "DECLINED"},
        headers=auth_header(second_user),
    )
    attendees = (await client.get(f"/api/v1/reunions/{rid}/attendees")).json()
    usernames = {a["username"] for a in attendees}
    assert "alice" in usernames  # host going
    assert "carol" not in usernames  # declined


async def test_reunion_not_found(client, user):
    r = await client.get(f"/api/v1/reunions/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_rsvp_requires_auth(client, user):
    _, r = await _school_and_reunion(client, user)
    rid = r.json()["id"]
    resp = await client.put(f"/api/v1/reunions/{rid}/rsvp", json={"status": "GOING"})
    assert resp.status_code == 401
