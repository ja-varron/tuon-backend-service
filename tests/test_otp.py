"""
Tests for POST /api/v1/auth/otp/verify (OTP verification).

Covered cases:
- Valid OTP → 200 + account created
- No active OTP flow → 400
- Max attempts reached → 429
- Wrong OTP → 401
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


def _make_flow(otp_flow_id="flow-uuid", otp_hash="$2b$12$hash", attempts=0, institution_name="Test University"):
    """Helper: build a mock OTP flow row."""
    flow = MagicMock()
    flow.otp_flow_id = otp_flow_id
    flow.otp_hash = otp_hash
    flow.attempts = attempts
    flow.institution_name = institution_name
    return flow


def _make_user(user_id="user-uuid"):
    user = MagicMock()
    user.user_id = user_id
    return user


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_otp_verify_success(client, mock_db):
    """Correct OTP verifies account and creates institution + profile."""
    flow = _make_flow()
    user = _make_user()

    with patch("services.auth.otp.otp_flows.get_active_otp_flow", return_value=flow), \
         patch("services.auth.otp.verify_password", return_value=True), \
         patch("services.auth.otp.otp_flows.invalidate_otp_flow"), \
         patch("services.auth.otp.users.get_user_by_email", return_value=user), \
         patch("services.auth.otp.users.update_user_verification"), \
         patch("services.auth.otp.institutions.create_institution", return_value="inst-uuid"), \
         patch("services.auth.otp.profiles.create_admin_profile"):

        response = client.post("/api/v1/auth/otp/verify", json={
            "email": "admin@testuniversity.edu",
            "otp": "123456"
        })

    assert response.status_code == 200
    assert "verified" in response.json()["message"].lower()


# ---------------------------------------------------------------------------
# No active flow
# ---------------------------------------------------------------------------

def test_otp_verify_no_active_flow(client, mock_db):
    """When no active OTP exists, return 400."""
    with patch("services.auth.otp.otp_flows.get_active_otp_flow", return_value=None):

        response = client.post("/api/v1/auth/otp/verify", json={
            "email": "admin@testuniversity.edu",
            "otp": "123456"
        })

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Max attempts
# ---------------------------------------------------------------------------

def test_otp_verify_max_attempts(client, mock_db):
    """When OTP attempts are exhausted, return 429."""
    from core.config import settings
    flow = _make_flow(attempts=settings.OTP_MAX_ATTEMPTS)

    with patch("services.auth.otp.otp_flows.get_active_otp_flow", return_value=flow), \
         patch("services.auth.otp.otp_flows.invalidate_otp_flow"):

        response = client.post("/api/v1/auth/otp/verify", json={
            "email": "jhonanthony.a.varron@gmail.com",
            "otp": "000000"
        })

    assert response.status_code == 429


# ---------------------------------------------------------------------------
# Wrong OTP
# ---------------------------------------------------------------------------

def test_otp_verify_wrong_otp(client, mock_db):
    """An incorrect OTP increments attempts and returns 401."""
    flow = _make_flow()

    with patch("services.auth.otp.otp_flows.get_active_otp_flow", return_value=flow), \
         patch("services.auth.otp.verify_password", return_value=False), \
         patch("services.auth.otp.otp_flows.increment_attempts"):

        response = client.post("/api/v1/auth/otp/verify", json={
            "email": "jhonanthony.a.varron@gmail.com",
            "otp": "000000"
        })

    assert response.status_code == 401
