import uuid

from tests.conftest import auth_header


async def _school_and_reunion(client, user, starts_at="2026-08-15T18:00:00Z"):
    slug = (
        await client.post(
            "/api/v1/schools", json={"name": "CBNU"}, headers=auth_header(user)
        )
    ).json()["slug"]
    # Must join the school before hosting a reunion.
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    r = await client.post(
        f"/api/v1/schools/{slug}/reunions",
        json={
            "title": "15-Year Reunion",
            "class_year": 2011,
            "starts_at": starts_at,
            "venue": "The Grand Lawn",
            "city": "Cheongju",
            "amenities": ["Dinner included", "Live band"],
        },
        headers=auth_header(user),
    )
    return slug, r


async def test_create_reunion_requires_membership(client, user, second_user):
    # alice creates+joins the school; carol (not a member) cannot host a reunion.
    slug, _ = await _school_and_reunion(client, user)
    r = await client.post(
        f"/api/v1/schools/{slug}/reunions",
        json={"title": "Crash", "starts_at": "2026-09-01T18:00:00Z"},
        headers=auth_header(second_user),
    )
    assert r.status_code == 403, r.text


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
    attendees = (
        await client.get(f"/api/v1/reunions/{rid}/attendees", headers=auth_header(user))
    ).json()
    usernames = {a["username"] for a in attendees}
    assert "alice" in usernames  # host going
    assert "carol" not in usernames  # declined


async def test_list_attendees_requires_auth(client, user):
    _, r = await _school_and_reunion(client, user)
    rid = r.json()["id"]
    resp = await client.get(f"/api/v1/reunions/{rid}/attendees")  # no token
    assert resp.status_code == 401


async def test_list_reunions_excludes_past(client, user):
    # A past reunion must not appear in the "upcoming" list, but a future one must.
    slug, past = await _school_and_reunion(client, user, starts_at="2020-01-01T18:00:00Z")
    future = await client.post(
        f"/api/v1/schools/{slug}/reunions",
        json={"title": "Future Mixer", "starts_at": "2099-01-01T18:00:00Z"},
        headers=auth_header(user),
    )
    ids = {
        r["id"]
        for r in (await client.get("/api/v1/reunions", headers=auth_header(user))).json()
    }
    assert future.json()["id"] in ids
    assert past.json()["id"] not in ids


async def test_reunion_not_found(client, user):
    r = await client.get(f"/api/v1/reunions/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_rsvp_requires_auth(client, user):
    _, r = await _school_and_reunion(client, user)
    rid = r.json()["id"]
    resp = await client.put(f"/api/v1/reunions/{rid}/rsvp", json={"status": "GOING"})
    assert resp.status_code == 401
