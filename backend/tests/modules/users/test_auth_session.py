import pytest
from fastapi.testclient import TestClient

from keepyourid.config import get_settings
from keepyourid.core.auth import SESSION_COOKIE_NAME, get_db
from keepyourid.main import app


@pytest.fixture
def client(db_session):
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def register_user(client, email="user@example.com", password="password123"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Session User",
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response


def login(client, email="user@example.com", password="password123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_login_sets_session_cookie_attributes(client):
    register_user(client)
    response = login(client)

    assert response.status_code == 200, response.text

    set_cookie = response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/" in set_cookie
    assert "Max-Age=604800" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "secure" not in set_cookie.lower().replace("samesite", "")


def test_login_cookie_attributes_cross_site(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "session_cookie_samesite", "none")
    monkeypatch.setattr(settings, "session_cookie_secure", None)

    register_user(client, email="cross@example.com")
    response = login(client, email="cross@example.com")

    assert response.status_code == 200, response.text
    set_cookie = response.headers["set-cookie"]
    assert "SameSite=none" in set_cookie
    assert "Secure" in set_cookie


def test_me_without_cookie_returns_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_valid_session_cookie_returns_user(client):
    register_user(client, email="me@example.com")
    login_response = login(client, email="me@example.com")
    assert login_response.status_code == 200

    # TestClient persists cookies set by the login response
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200, response.text
    assert response.json()["email"] == "me@example.com"


def test_logout_revokes_session_and_clears_cookie(client):
    register_user(client, email="logout@example.com")
    login(client, email="logout@example.com")

    token = client.cookies.get(SESSION_COOKIE_NAME)
    assert token

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    set_cookie = logout_response.headers["set-cookie"]
    assert SESSION_COOKIE_NAME in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()

    # Cookie removed from the jar by delete_cookie
    assert client.cookies.get(SESSION_COOKIE_NAME) is None

    # Session revoked server-side: the old token must no longer authenticate
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
