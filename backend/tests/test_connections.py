from tests.conftest import auth_header


async def test_request_and_accept_connection(client, user, second_user):
    alice, carol = user, second_user
    carol_id = carol["user"]["id"]
    alice_id = alice["user"]["id"]

    # alice requests carol
    r = await client.post(
        "/api/v1/connections", json={"user_id": carol_id}, headers=auth_header(alice)
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "PENDING"

    # carol sees an incoming request
    reqs = (
        await client.get("/api/v1/connections/requests", headers=auth_header(carol))
    ).json()
    assert {x["username"] for x in reqs} == {"alice"}

    # carol accepts
    acc = await client.post(
        f"/api/v1/connections/{alice_id}/accept", headers=auth_header(carol)
    )
    assert acc.json()["status"] == "ACCEPTED"

    # both now list each other as a connection
    alice_conns = (await client.get("/api/v1/connections", headers=auth_header(alice))).json()
    assert {c["username"] for c in alice_conns} == {"carol"}


async def test_reverse_request_auto_accepts(client, user, second_user):
    alice, carol = user, second_user
    await client.post(
        "/api/v1/connections", json={"user_id": carol["user"]["id"]},
        headers=auth_header(alice),
    )
    # carol requesting alice back should accept the pending request
    r = await client.post(
        "/api/v1/connections", json={"user_id": alice["user"]["id"]},
        headers=auth_header(carol),
    )
    assert r.json()["status"] == "ACCEPTED"


async def test_duplicate_request_is_idempotent(client, user, second_user):
    alice, carol = user, second_user
    body = {"user_id": carol["user"]["id"]}
    r1 = await client.post("/api/v1/connections", json=body, headers=auth_header(alice))
    r2 = await client.post("/api/v1/connections", json=body, headers=auth_header(alice))
    assert r1.status_code == 201, r1.text
    assert r2.status_code in (200, 201), r2.text  # idempotent, no 500
    assert r2.json()["status"] == "PENDING"
    # carol sees exactly one pending request
    reqs = (
        await client.get("/api/v1/connections/requests", headers=auth_header(carol))
    ).json()
    assert len(reqs) == 1


async def test_cannot_connect_to_self(client, user):
    r = await client.post(
        "/api/v1/connections", json={"user_id": user["user"]["id"]},
        headers=auth_header(user),
    )
    assert r.status_code == 400


async def test_remove_connection(client, user, second_user):
    alice, carol = user, second_user
    cr = await client.post(
        "/api/v1/connections", json={"user_id": carol["user"]["id"]},
        headers=auth_header(alice),
    )
    assert cr.status_code == 201, cr.text
    r = await client.delete(
        f"/api/v1/connections/{carol['user']['id']}", headers=auth_header(alice)
    )
    assert r.status_code == 204, r.text
    conns = (await client.get("/api/v1/connections", headers=auth_header(alice))).json()
    assert conns == []


async def test_suggestions_excludes_connected_and_self(client, user, second_user):
    alice, carol = user, second_user
    slug = (
        await client.post("/api/v1/schools", json={"name": "CBNU"}, headers=auth_header(alice))
    ).json()["slug"]
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(alice))
    await client.post(f"/api/v1/schools/{slug}/join", headers=auth_header(carol))

    # before connecting, carol is suggested to alice
    sugg = (
        await client.get("/api/v1/connections/suggestions", headers=auth_header(alice))
    ).json()
    assert "carol" in {s["username"] for s in sugg}

    # after a pending request, carol drops out of suggestions
    await client.post(
        "/api/v1/connections", json={"user_id": carol["user"]["id"]},
        headers=auth_header(alice),
    )
    sugg2 = (
        await client.get("/api/v1/connections/suggestions", headers=auth_header(alice))
    ).json()
    assert "carol" not in {s["username"] for s in sugg2}
