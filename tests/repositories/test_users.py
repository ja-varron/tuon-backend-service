"""
Tests for src/repositories/users.py
This file tests the SQL statements executed in the users repository.
"""
import pytest
from unittest.mock import MagicMock
from repositories.users import (
    get_user_by_email,
    create_user,
    update_user_verification,
    update_user_password,
)

pytestmark = pytest.mark.anyio

async def test_get_user_by_email(mock_db):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = {"user_id": "new-uuid"}
    mock_db.execute.return_value = mock_result

    email = "test@example.com"
    result = await get_user_by_email(mock_db, email)

    mock_db.execute.assert_called_once()
    args, kwargs = mock_db.execute.call_args
    executed_query = args[0]

    assert "SELECT * FROM tuon_auth.users WHERE email = :email" in str(executed_query)
    assert args[1] == {"email": email}
    assert result == {"user_id": "new-uuid"}

async def test_create_user(mock_db):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = {"user_id": "new-uuid"}
    mock_db.execute.return_value = mock_result

    email = "test@example.com"
    hashed_password = "hashed_secret"

    result = await create_user(mock_db, email, hashed_password)

    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

    args, kwargs = mock_db.execute.call_args
    executed_stmt = args[0]
    compiled_stmt = str(executed_stmt.compile(compile_kwargs={"literal_binds": False}))

    assert "INSERT INTO tuon_auth.users" in compiled_stmt
    assert "email" in compiled_stmt
    assert "encrypted_password" in compiled_stmt
    assert result == "new-uuid"

async def test_update_user_verification(mock_db):
    user_id = "user-123"
    verified_at = "2026-09-04T12:00:00Z"

    await update_user_verification(mock_db, user_id, verified_at)

    mock_db.execute.assert_called_once()
    args, kwargs = mock_db.execute.call_args
    executed_stmt = args[0]
    compiled_stmt = str(executed_stmt.compile(compile_kwargs={"literal_binds": False}))

    assert "UPDATE tuon_auth.users" in compiled_stmt
    assert "confirmed_created_at" in compiled_stmt
    assert "WHERE user_id" in compiled_stmt

async def test_update_user_password(mock_db):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = {"user_id": "user-123"}
    mock_db.execute.return_value = mock_result

    email = "test@example.com"
    hashed_password = "new_hashed_password"

    await update_user_password(mock_db, email, hashed_password)

    mock_db.execute.assert_called_once()
    args, kwargs = mock_db.execute.call_args
    executed_stmt = args[0]
    compiled_stmt = str(executed_stmt.compile(compile_kwargs={"literal_binds": False}))

    assert "UPDATE tuon_auth.users" in compiled_stmt
    assert "encrypted_password" in compiled_stmt
    assert "WHERE email" in compiled_stmt
