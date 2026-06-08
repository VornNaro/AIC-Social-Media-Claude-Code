import uuid

from tests.conftest import auth_header


async def test_share_post(client, post, second_user):
    r = await client.post(
        f"/api/v1/posts/{post['id']}/shares", headers=auth_header(second_user)
    )
    assert r.status_code == 200
    assert r.json()["share_count"] == 1
    assert r.json()["shared_by_me"] is True


async def test_duplicate_share_is_idempotent(client, post, second_user):
    h = auth_header(second_user)
    await client.post(f"/api/v1/posts/{post['id']}/shares", headers=h)
    r = await client.post(f"/api/v1/posts/{post['id']}/shares", headers=h)
    assert r.status_code == 200
    assert r.json()["share_count"] == 1  # still one


async def test_unshare(client, post, second_user):
    h = auth_header(second_user)
    await client.post(f"/api/v1/posts/{post['id']}/shares", headers=h)
    r = await client.delete(f"/api/v1/posts/{post['id']}/shares", headers=h)
    assert r.status_code == 200
    assert r.json()["share_count"] == 0
    assert r.json()["shared_by_me"] is False


async def test_share_missing_post(client, second_user):
    r = await client.post(
        f"/api/v1/posts/{uuid.uuid4()}/shares", headers=auth_header(second_user)
    )
    assert r.status_code == 404


async def test_shared_post_appears_in_feed(client, post, second_user):
    await client.post(f"/api/v1/posts/{post['id']}/shares", headers=auth_header(second_user))
    feed = (await client.get("/api/v1/posts", headers=auth_header(second_user))).json()
    reposts = [item for item in feed["items"] if item["shared_by"] is not None]
    assert len(reposts) == 1
    assert reposts[0]["shared_by"]["username"] == "carol"
    assert reposts[0]["id"] == post["id"]
