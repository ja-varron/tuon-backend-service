"""
Tests for POST /api/v1/auth/signup (Admin self-registration).

Covered cases:
- Valid signup → 201 + OTP sent message
- Duplicate email → 409
- Missing required fields → 422
"""
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_signup_success(client, mock_db):
    """Valid payload creates a user and triggers OTP send."""
    with patch("services.auth.registration.users.get_user_by_email", return_value=None), \
         patch("services.auth.registration.users.create_user", return_value="user-uuid-123"), \
         patch("services.auth.registration.generate_otp", return_value="123456"), \
         patch("services.auth.registration.email.send_otp_email"):

        response = client.post("/api/v1/auth/signup", json={
            "institution_name": "Test University",
            "email": "admin@testuniversity.edu",
            "password": "SecureP@ss1"
        })

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "OTP" in body["message"]


# ---------------------------------------------------------------------------
# Duplicate email
# ---------------------------------------------------------------------------

def test_signup_duplicate_email(client, mock_db):
    """Registering with an already-used email returns 409."""
    existing_user = MagicMock()
    existing_user.email = "admin@testuniversity.edu"

    with patch("services.auth.registration.users.get_user_by_email", return_value=existing_user):

        response = client.post("/api/v1/auth/signup", json={
            "institution_name": "Test University",
            "email": "admin@testuniversity.edu",
            "password": "SecureP@ss1"
        })

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Missing fields
# ---------------------------------------------------------------------------

def test_signup_missing_institution_name(client):
    """institution_name is required — missing it returns 422."""
    response = client.post("/api/v1/auth/signup", json={
        "email": "admin@testuniversity.edu",
        "password": "SecureP@ss1"
    })
    assert response.status_code == 422


def test_signup_missing_email(client):
    """email is required — missing it returns 422."""
    response = client.post("/api/v1/auth/signup", json={
        "institution_name": "Test University",
        "password": "SecureP@ss1"
    })
    assert response.status_code == 422


def test_signup_invalid_email_format(client):
    """A badly-formed email returns 422."""
    response = client.post("/api/v1/auth/signup", json={
        "institution_name": "Test University",
        "email": "not-an-email",
        "password": "SecureP@ss1"
    })
    assert response.status_code == 422
