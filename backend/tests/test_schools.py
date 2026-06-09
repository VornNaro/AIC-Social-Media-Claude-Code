from tests.conftest import auth_header


async def _make_school(client, user, name="Chungbuk National University", **extra):
    body = {"name": name, **extra}
    return await client.post("/api/v1/schools", json=body, headers=auth_header(user))


async def test_create_school_returns_slug(client, user):
    r = await _make_school(client, user, location="Cheongju", founded=1951)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["slug"] == "chungbuk-national-university"
    assert data["founded"] == 1951
    assert data["member_count"] == 0


async def test_create_school_is_find_or_create(client, user, second_user):
    r1 = await _make_school(client, user)
    r2 = await _make_school(client, second_user)  # same name → same school
    assert r1.json()["id"] == r2.json()["id"]


async def test_join_and_leave_school(client, user):
    slug = (await _make_school(client, user)).json()["slug"]
    r = await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    assert r.status_code == 200
    assert r.json()["is_member"] is True
    assert r.json()["member_count"] == 1

    # idempotent re-join
    r2 = await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    assert r2.json()["member_count"] == 1

    r3 = await client.delete(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    assert r3.json()["is_member"] is False
    assert r3.json()["member_count"] == 0


async def test_members_directory_filters_by_year(client, user, second_user):
    slug = (await _make_school(client, user)).json()["slug"]
    # set grad years + join
    await client.patch(
        "/api/v1/users/me", json={"graduation_year": 2012}, headers=auth_header(user)
    )
    await client.patch(
        "/api/v1/users/me", json={"graduation_year": 2011}, headers=auth_header(second_user)
    )
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(second_user))

    # carol (second_user) viewing: directory excludes self, alice is 2012
    all_members = (
        await client.get(f"/api/v1/schools/{slug}/members", headers=auth_header(second_user))
    ).json()
    assert {m["username"] for m in all_members} == {"alice"}

    none_2009 = (
        await client.get(
            f"/api/v1/schools/{slug}/members?year=2009", headers=auth_header(second_user)
        )
    ).json()
    assert none_2009 == []


async def test_members_search_escapes_like_wildcards(client, user, second_user):
    slug = (await _make_school(client, user)).json()["slug"]
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(user))
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(second_user))
    # "%" is a LIKE wildcard; escaped, it matches only a literal "%", which no
    # display_name/city contains — so the result is empty, not "everyone".
    res = (
        await client.get(
            f"/api/v1/schools/{slug}/members?q=%25", headers=auth_header(user)
        )
    ).json()
    assert res == []


async def test_school_not_found(client, user):
    r = await client.get("/api/v1/schools/nope", headers=auth_header(user))
    assert r.status_code == 404


async def test_create_school_requires_auth(client):
    r = await client.post("/api/v1/schools", json={"name": "Anon High"})
    assert r.status_code == 401
