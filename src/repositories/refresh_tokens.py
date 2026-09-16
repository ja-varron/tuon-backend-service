"""
Refresh token repository.

All DB operations for the refresh_tokens table.
Tokens are stored as SHA-256 hashes — never the raw value.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from core.config import settings

REFRESH_TOKENS_TABLE = 'tuon_auth.refresh_tokens'

def _hash_token(raw_token: str) -> str:
    """Returns the SHA-256 hex digest of the raw token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_raw_token() -> str:
    """
    Generates a cryptographically secure random refresh token string.
    The caller receives this raw value; only its hash is persisted.
    """
    return secrets.token_urlsafe(64)


async def create_refresh_token(db: AsyncSession, user_id: str) -> str:
    """
    Creates and stores a new refresh token for the given user.

    Args:
        db: Database session
        user_id: The authenticated user's UUID

    Returns:
        str: The raw (unhashed) refresh token to send to the client.
    """
    raw_token = generate_raw_token()
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    sql_statement = text(f"""
        INSERT INTO {REFRESH_TOKENS_TABLE} (user_id, token_hash, expires_at)
        VALUES (:user_id, :token_hash, :expires_at)
    """)

    await db.execute(sql_statement, {
        'user_id': user_id,
        'token_hash': token_hash,
        'expires_at': expires_at
    })
    await db.commit()

    return raw_token


async def get_valid_refresh_token(db: AsyncSession, raw_token: str):
    """
    Looks up a refresh token by its hash and ensures it is:
      - not revoked (revoked_at IS NULL)
      - not expired (expires_at > now)

    Args:
        db: Database session
        raw_token: The raw token string sent by the client

    Returns:
        Row mapping or None
    """

    token_hash = _hash_token(raw_token)

    sql_statement = text(f"""
        SELECT * FROM {REFRESH_TOKENS_TABLE}
        WHERE token_hash = :token_hash
        AND revoked_at IS NULL
        AND expires_at > :now
    """)

    result = await db.execute(sql_statement, {
        'token_hash': token_hash,
        'now': datetime.now(timezone.utc)
    })

    await db.commit()  # Commit the transaction to ensure consistency
    return result.mappings().first()


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> bool:
    """
    Revokes a single refresh token (signout from one device).

    Args:
        db: Database session
        raw_token: The raw token string sent by the client

    Returns:
        bool: True if a token was found and revoked, False otherwise.
    """
    token_hash = _hash_token(raw_token)

    sql_statement = text(f"""
        UPDATE {REFRESH_TOKENS_TABLE}
        SET revoked_at = :now
        WHERE token_hash = :token_hash
        AND revoked_at IS NULL
    """)

    result = await db.execute(sql_statement, {
        'token_hash': token_hash,
        'now': datetime.now(timezone.utc)
    })
    await db.commit()
    return result.rowcount > 0


async def revoke_all_user_tokens(db: AsyncSession, user_id: str):
    """
    Revokes all active refresh tokens for a user (signout from all devices).

    Args:
        db: Database session
        user_id: The user's UUID
    """

    sql_statement = text(f"""
        UPDATE {REFRESH_TOKENS_TABLE}
        SET revoked_at = :now
        WHERE user_id = :user_id
        AND revoked_at IS NULL
    """)

    await db.execute(sql_statement, {'user_id': user_id, 'revoked_at': datetime.now(timezone.utc)})
    await db.commit()
