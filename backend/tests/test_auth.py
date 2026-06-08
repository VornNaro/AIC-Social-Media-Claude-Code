BASE = "/api/v1/auth"


# --- register -------------------------------------------------------------

async def test_register_success(client):
    r = await client.post(
        f"{BASE}/register",
        json={"username": "bob", "email": "bob@example.com", "password": "password123"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["access_token"] and data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "bob"
    # display_name defaults to username when omitted
    assert data["user"]["display_name"] == "bob"
    # secrets never leak
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


async def test_register_duplicate_username(client, user):
    r = await client.post(
        f"{BASE}/register",
        json={"username": "alice", "email": "other@example.com", "password": "password123"},
    )
    assert r.status_code == 409


async def test_register_duplicate_email(client, user):
    r = await client.post(
        f"{BASE}/register",
        json={"username": "other", "email": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 409


async def test_register_weak_password(client):
    r = await client.post(
        f"{BASE}/register",
        json={"username": "weak", "email": "weak@example.com", "password": "short"},
    )
    assert r.status_code == 422


async def test_register_invalid_username(client):
    r = await client.post(
        f"{BASE}/register",
        json={"username": "bad name!", "email": "x@example.com", "password": "password123"},
    )
    assert r.status_code == 422


# --- login ----------------------------------------------------------------

async def test_login_with_username(client, user):
    r = await client.post(
        f"{BASE}/login", json={"username_or_email": "alice", "password": "password123"}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


async def test_login_with_email(client, user):
    r = await client.post(
        f"{BASE}/login",
        json={"username_or_email": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 200


async def test_login_wrong_password(client, user):
    r = await client.post(
        f"{BASE}/login", json={"username_or_email": "alice", "password": "wrongpass1"}
    )
    assert r.status_code == 401


async def test_login_unknown_user(client):
    r = await client.post(
        f"{BASE}/login", json={"username_or_email": "ghost", "password": "password123"}
    )
    assert r.status_code == 401


# --- me -------------------------------------------------------------------

async def test_me_requires_auth(client):
    r = await client.get(f"{BASE}/me")
    assert r.status_code == 401


async def test_me_success(auth_client):
    r = await auth_client.get(f"{BASE}/me")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"


async def test_me_garbage_token(client):
    client.headers["Authorization"] = "Bearer not.a.real.jwt"
    r = await client.get(f"{BASE}/me")
    assert r.status_code == 401


# --- refresh rotation + reuse detection -----------------------------------

async def test_refresh_rotates(client, user):
    old = user["refresh_token"]
    r = await client.post(f"{BASE}/refresh", json={"refresh_token": old})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != old
    # the old refresh token is now invalid
    again = await client.post(f"{BASE}/refresh", json={"refresh_token": old})
    assert again.status_code == 401


async def test_refresh_reuse_revokes_all(client, user):
    old = user["refresh_token"]
    rotated = (await client.post(f"{BASE}/refresh", json={"refresh_token": old})).json()
    new = rotated["refresh_token"]
    # reuse the already-rotated token -> theft signal -> revoke everything
    reuse = await client.post(f"{BASE}/refresh", json={"refresh_token": old})
    assert reuse.status_code == 401
    # even the freshly issued token is now revoked
    after = await client.post(f"{BASE}/refresh", json={"refresh_token": new})
    assert after.status_code == 401


async def test_refresh_rejects_access_token(client, user):
    # an access token must not be accepted at the refresh endpoint
    r = await client.post(f"{BASE}/refresh", json={"refresh_token": user["access_token"]})
    assert r.status_code == 401


# --- logout ---------------------------------------------------------------

async def test_logout_then_refresh_fails(client, user):
    r = await client.post(f"{BASE}/logout", json={"refresh_token": user["refresh_token"]})
    assert r.status_code == 204
    after = await client.post(
        f"{BASE}/refresh", json={"refresh_token": user["refresh_token"]}
    )
    assert after.status_code == 401
