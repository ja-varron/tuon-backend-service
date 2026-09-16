"""Route tests for refresh tokens, signout, and bearer-token authorization."""
from unittest.mock import AsyncMock, patch

from schemas.auth.tokens import TokenPayload


def test_refresh_token_success(client, mock_db):
    with patch("services.auth.tokens.tokens_repo.get_valid_refresh_token", new_callable=AsyncMock,
               return_value={"user_id": "user-uuid"}), \
         patch("services.auth.tokens.profiles_repo.get_profile_by_user_id", new_callable=AsyncMock,
               return_value={"role": "admin", "institution_id": "inst-uuid"}), \
         patch("services.auth.tokens.tokens_repo.revoke_refresh_token", new_callable=AsyncMock), \
         patch("services.auth.tokens.tokens_repo.create_refresh_token", new_callable=AsyncMock,
               return_value="new-refresh"), \
         patch("services.auth.tokens.create_access_token", return_value="new-access"):
        response = client.post("/api/v1/auth/token/refresh", json={"refresh_token": "old-refresh"})

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access", "refresh_token": "new-refresh", "token_type": "bearer"
    }


def test_refresh_token_invalid_returns_401(client, mock_db):
    with patch("services.auth.tokens.tokens_repo.get_valid_refresh_token", new_callable=AsyncMock,
               return_value=None):
        response = client.post("/api/v1/auth/token/refresh", json={"refresh_token": "invalid"})
    assert response.status_code == 401


def test_signout_success(client, mock_db):
    with patch("services.auth.tokens.tokens_repo.revoke_refresh_token", new_callable=AsyncMock,
               return_value=True) as revoke:
        response = client.post("/api/v1/auth/signout", json={"refresh_token": "refresh"})
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully signed out"
    revoke.assert_awaited_once_with(mock_db, "refresh")


def test_signout_unknown_token_returns_401(client, mock_db):
    with patch("services.auth.tokens.tokens_repo.revoke_refresh_token", new_callable=AsyncMock,
               return_value=False):
        response = client.post("/api/v1/auth/signout", json={"refresh_token": "unknown"})
    assert response.status_code == 401


def test_signout_all_requires_bearer_token(client):
    response = client.post("/api/v1/auth/signout/all")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_signout_all_success_for_authenticated_user(client, mock_db):
    from core.security import get_current_user
    from main import app

    app.dependency_overrides[get_current_user] = lambda: TokenPayload(
        sub="user-uuid", role="admin", institution_id="inst-uuid"
    )
    try:
        with patch("services.auth.tokens.tokens_repo.revoke_all_user_tokens", new_callable=AsyncMock) as revoke:
            response = client.post("/api/v1/auth/signout/all")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully signed out from all devices"
        revoke.assert_awaited_once_with(mock_db, "user-uuid")
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_signout_all_rejects_invalid_bearer_token(client):
    response = client.post("/api/v1/auth/signout/all", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401