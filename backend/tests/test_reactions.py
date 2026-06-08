import uuid

from tests.conftest import auth_header


async def test_add_reaction(client, user, post):
    r = await client.put(
        f"/api/v1/posts/{post['id']}/reactions",
        json={"type": "LIKE"},
        headers=auth_header(user),
    )
    assert r.status_code == 200
    assert r.json()["reaction_counts"] == {"LIKE": 1}
    assert r.json()["my_reaction"] == "LIKE"


async def test_same_reaction_toggles_off(client, user, post):
    h = auth_header(user)
    await client.put(f"/api/v1/posts/{post['id']}/reactions", json={"type": "LIKE"}, headers=h)
    r = await client.put(
        f"/api/v1/posts/{post['id']}/reactions", json={"type": "LIKE"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["my_reaction"] is None
    assert r.json()["reaction_counts"] == {}


async def test_switching_reaction_keeps_single_row(client, user, post, db):
    from sqlalchemy import func, select

    from app.models.reaction import Reaction

    h = auth_header(user)
    await client.put(f"/api/v1/posts/{post['id']}/reactions", json={"type": "LIKE"}, headers=h)
    r = await client.put(
        f"/api/v1/posts/{post['id']}/reactions", json={"type": "LOVE"}, headers=h
    )
    assert r.json()["reaction_counts"] == {"LOVE": 1}
    assert r.json()["my_reaction"] == "LOVE"
    rows = await db.scalar(select(func.count()).select_from(Reaction))
    assert rows == 1  # unique constraint honored — switched in place


async def test_two_users_aggregate(client, user, post, second_user):
    await client.put(
        f"/api/v1/posts/{post['id']}/reactions",
        json={"type": "LIKE"},
        headers=auth_header(user),
    )
    r = await client.put(
        f"/api/v1/posts/{post['id']}/reactions",
        json={"type": "LIKE"},
        headers=auth_header(second_user),
    )
    assert r.json()["reaction_counts"] == {"LIKE": 2}
    # each user sees their own reaction
    assert r.json()["my_reaction"] == "LIKE"


async def test_delete_reaction(client, user, post):
    h = auth_header(user)
    await client.put(f"/api/v1/posts/{post['id']}/reactions", json={"type": "WOW"}, headers=h)
    r = await client.delete(f"/api/v1/posts/{post['id']}/reactions", headers=h)
    assert r.status_code == 200
    assert r.json()["reaction_counts"] == {}


async def test_invalid_reaction_type(client, user, post):
    r = await client.put(
        f"/api/v1/posts/{post['id']}/reactions",
        json={"type": "THUMBSUP"},
        headers=auth_header(user),
    )
    assert r.status_code == 422


async def test_reaction_on_missing_post(client, user):
    r = await client.put(
        f"/api/v1/posts/{uuid.uuid4()}/reactions",
        json={"type": "LIKE"},
        headers=auth_header(user),
    )
    assert r.status_code == 404
