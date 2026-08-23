"""
Tests for POST /api/v1/auth/signin.

Covered cases:
- Valid credentials → 200 + JWT token
- Unknown email → 401
- Wrong password → 401
- Unverified account (email_created_at is None) → 401
"""
import pytest
from unittest.mock import patch, MagicMock


def _make_user(user_id="user-uuid", email_created_at="2026-01-01T00:00:00Z"):
    user = MagicMock()
    user.user_id = user_id
    user.encrypted_password = "$2b$12$hashedpassword"
    user.email_created_at = email_created_at
    return user


def _make_profile(role="admin", institution_id="inst-uuid"):
    profile = MagicMock()
    profile.role = role
    profile.institution_id = institution_id
    profile.first_name = "Test University"
    profile.last_name = "Administrator"
    return profile


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_signin_success(client, mock_db):
    """Valid credentials return a JWT access token."""
    user = _make_user()
    profile = _make_profile()

    with patch("services.auth.login.users.get_user_by_email", return_value=user), \
         patch("services.auth.login.verify_password", return_value=True), \
         patch("services.auth.login.profiles.get_profile_by_user_id", return_value=profile), \
         patch("services.auth.login.create_access_token", return_value="mocked.jwt.token"):

        response = client.post("/api/v1/auth/signin", json={
            "email": "admin@testuniversity.edu",
            "password": "SecureP@ss1"
        })

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "mocked.jwt.token"
    assert body["token_type"] == "bearer"
    assert body["profile"]["role"] == "admin"


# ---------------------------------------------------------------------------
# Unknown email
# ---------------------------------------------------------------------------

def test_signin_unknown_email(client, mock_db):
    """An email not in the DB returns 401."""
    with patch("services.auth.login.users.get_user_by_email", return_value=None):

        response = client.post("/api/v1/auth/signin", json={
            "email": "ghost@nowhere.com",
            "password": "SecureP@ss1"
        })

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Wrong password
# ---------------------------------------------------------------------------

def test_signin_wrong_password(client, mock_db):
    """A wrong password returns 401."""
    user = _make_user()

    with patch("services.auth.login.users.get_user_by_email", return_value=user), \
         patch("services.auth.login.verify_password", return_value=False):

        response = client.post("/api/v1/auth/signin", json={
            "email": "admin@testuniversity.edu",
            "password": "WrongPassword!"
        })

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Unverified account
# ---------------------------------------------------------------------------

def test_signin_unverified_account(client, mock_db):
    """A user who hasn't completed OTP verification returns 401."""
    user = _make_user(email_created_at=None)

    with patch("services.auth.login.users.get_user_by_email", return_value=user), \
         patch("services.auth.login.verify_password", return_value=True):

        response = client.post("/api/v1/auth/signin", json={
            "email": "admin@testuniversity.edu",
            "password": "SecureP@ss1"
        })

    assert response.status_code == 401
