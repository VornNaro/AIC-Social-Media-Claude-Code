import uuid

from tests.conftest import auth_header


async def test_create_text_post(client, user):
    r = await client.post(
        "/api/v1/posts", json={"content": "Hello!"}, headers=auth_header(user)
    )
    assert r.status_code == 201
    data = r.json()
    assert data["content"] == "Hello!"
    assert data["author"]["username"] == "alice"
    assert data["reaction_counts"] == {}
    assert data["comment_count"] == 0
    assert data["share_count"] == 0
    assert data["my_reaction"] is None


async def test_create_image_post(client, user):
    r = await client.post(
        "/api/v1/posts",
        json={"image_url": "https://example.com/cat.png"},
        headers=auth_header(user),
    )
    assert r.status_code == 201
    assert r.json()["image_url"].endswith("cat.png")


async def test_create_requires_content_or_image(client, user):
    r = await client.post("/api/v1/posts", json={}, headers=auth_header(user))
    assert r.status_code == 422


async def test_create_requires_auth(client):
    r = await client.post("/api/v1/posts", json={"content": "hi"})
    assert r.status_code == 401


async def test_get_post(client, post):
    r = await client.get(f"/api/v1/posts/{post['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == post["id"]


async def test_get_post_404(client):
    r = await client.get(f"/api/v1/posts/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_patch_own_post(client, user, post):
    r = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"content": "edited"},
        headers=auth_header(user),
    )
    assert r.status_code == 200
    assert r.json()["content"] == "edited"


async def test_patch_others_post_forbidden(client, post, second_user):
    r = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"content": "hijack"},
        headers=auth_header(second_user),
    )
    assert r.status_code == 403


async def test_delete_post(client, user, post):
    r = await client.delete(f"/api/v1/posts/{post['id']}", headers=auth_header(user))
    assert r.status_code == 204
    gone = await client.get(f"/api/v1/posts/{post['id']}")
    assert gone.status_code == 404


async def test_delete_cascades_comments(client, user, post, db):
    from sqlalchemy import func, select

    from app.models.comment import Comment

    await client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"content": "hi"},
        headers=auth_header(user),
    )
    await client.delete(f"/api/v1/posts/{post['id']}", headers=auth_header(user))
    count = await db.scalar(select(func.count()).select_from(Comment))
    assert count == 0


async def test_feed_pagination(client, user):
    for i in range(25):
        await client.post(
            "/api/v1/posts", json={"content": f"post {i}"}, headers=auth_header(user)
        )
    first = (await client.get("/api/v1/posts?limit=20")).json()
    assert len(first["items"]) == 20
    assert first["has_more"] is True
    assert first["next_cursor"]

    second = (
        await client.get(f"/api/v1/posts?limit=20&cursor={first['next_cursor']}")
    ).json()
    assert len(second["items"]) == 5
    assert second["has_more"] is False

    first_ids = {p["id"] for p in first["items"]}
    second_ids = {p["id"] for p in second["items"]}
    assert first_ids.isdisjoint(second_ids)  # no overlap between pages


async def test_patch_to_empty_content_rejected(client, user, post):
    # post has text content and no image; blanking the content must be refused
    r = await client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"content": "   "},
        headers=auth_header(user),
    )
    assert r.status_code == 400


async def test_invalid_cursor_returns_422(client, post):
    r = await client.get("/api/v1/posts?cursor=not-a-valid-cursor")
    assert r.status_code == 422


async def test_unauthenticated_feed_has_no_personalization(client, post):
    data = (await client.get("/api/v1/posts")).json()
    assert data["items"][0]["my_reaction"] is None
    assert data["items"][0]["shared_by_me"] is False
