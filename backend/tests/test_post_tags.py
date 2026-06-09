from tests.conftest import auth_header


async def test_post_with_tags_and_note(client, user):
    r = await client.post(
        "/api/v1/posts",
        json={"content": "grad day", "tags": ["#SchoolDays", "#ClassOf2012"], "note": "Best ever"},
        headers=auth_header(user),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["tags"] == ["#SchoolDays", "#ClassOf2012"]
    assert body["note"] == "Best ever"


async def test_overlong_tag_rejected_with_422(client, user):
    # A tag longer than the DB column (60) must be a clean validation error, not a 500.
    r = await client.post(
        "/api/v1/posts",
        json={"content": "hi", "tags": ["#" + "x" * 80]},
        headers=auth_header(user),
    )
    assert r.status_code == 422, r.text


async def test_too_many_tags_rejected(client, user):
    r = await client.post(
        "/api/v1/posts",
        json={"content": "hi", "tags": [f"#t{i}" for i in range(11)]},
        headers=auth_header(user),
    )
    assert r.status_code == 422, r.text
