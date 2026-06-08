import uuid

from tests.conftest import auth_header


async def test_add_comment(client, user, post):
    r = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "nice post"},
        headers=auth_header(user),
    )
    assert r.status_code == 201
    assert r.json()["content"] == "nice post"
    assert r.json()["author"]["username"] == "alice"

    # comment_count reflected on the post
    p = (await client.get(f"/api/v1/posts/{post['id']}")).json()
    assert p["comment_count"] == 1


async def test_comment_max_length(client, user, post):
    ok = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "x" * 1000},
        headers=auth_header(user),
    )
    assert ok.status_code == 201
    too_long = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "x" * 1001},
        headers=auth_header(user),
    )
    assert too_long.status_code == 422


async def test_comment_empty_rejected(client, user, post):
    r = await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": ""},
        headers=auth_header(user),
    )
    assert r.status_code == 422


async def test_comment_on_missing_post(client, user):
    r = await client.post(
        f"/api/v1/posts/{uuid.uuid4()}/comments",
        json={"content": "hi"},
        headers=auth_header(user),
    )
    assert r.status_code == 404


async def test_list_comments_ascending_and_paginated(client, user, post):
    for i in range(25):
        await client.post(
            f"/api/v1/posts/{post['id']}/comments",
            json={"content": f"c{i}"},
            headers=auth_header(user),
        )
    first = (await client.get(f"/api/v1/posts/{post['id']}/comments?limit=20")).json()
    assert len(first["items"]) == 20
    assert first["has_more"] is True
    # ascending order: c0 first
    assert first["items"][0]["content"] == "c0"

    second = (
        await client.get(
            f"/api/v1/posts/{post['id']}/comments?limit=20&cursor={first['next_cursor']}"
        )
    ).json()
    assert len(second["items"]) == 5


async def test_delete_own_comment(client, user, post):
    cid = (
        await client.post(
            f"/api/v1/posts/{post['id']}/comments",
            json={"content": "mine"},
            headers=auth_header(user),
        )
    ).json()["id"]
    r = await client.delete(f"/api/v1/comments/{cid}", headers=auth_header(user))
    assert r.status_code == 204


async def test_delete_others_comment_forbidden(client, user, post, second_user):
    cid = (
        await client.post(
            f"/api/v1/posts/{post['id']}/comments",
            json={"content": "mine"},
            headers=auth_header(user),
        )
    ).json()["id"]
    r = await client.delete(f"/api/v1/comments/{cid}", headers=auth_header(second_user))
    assert r.status_code == 403
