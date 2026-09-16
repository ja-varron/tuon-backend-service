"""Tests for the reusable role-based authorization dependency."""
import pytest
from fastapi import HTTPException

from core.security import require_role
from schemas.auth.tokens import TokenPayload


def test_require_role_allows_matching_role():
    current_user = TokenPayload(sub="user-uuid", role="admin", institution_id="inst-uuid")

    assert require_role("admin")(current_user) == current_user


def test_require_role_rejects_non_matching_role():
    current_user = TokenPayload(sub="user-uuid", role="examinee", institution_id="inst-uuid")

    with pytest.raises(HTTPException) as error:
        require_role("admin")(current_user)

    assert error.value.status_code == 403
    assert error.value.detail == "Access denied. Required role(s): admin"