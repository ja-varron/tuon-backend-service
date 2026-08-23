"""
Refresh token repository.

All DB operations for the refresh_tokens table.
Tokens are stored as SHA-256 hashes — never the raw value.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update

from db.connection import metadata
from core.config import settings

# Table reference — reflected automatically on startup
_MIGRATION_HINT = (
    "The 'refresh_tokens' table is missing from the database. "
    "Run sql/add_refresh_tokens_table.sql in your Supabase SQL Editor first."
)
try:
    refresh_tokens_table = metadata.tables['refresh_tokens']
except KeyError:
    raise RuntimeError(_MIGRATION_HINT)


def _hash_token(raw_token: str) -> str:
    """Returns the SHA-256 hex digest of the raw token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_raw_token() -> str:
    """
    Generates a cryptographically secure random refresh token string.
    The caller receives this raw value; only its hash is persisted.
    """
    return secrets.token_urlsafe(64)


def create_refresh_token(db: Session, user_id: str) -> str:
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
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    stmt = insert(refresh_tokens_table).values(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.execute(stmt)
    db.commit()

    return raw_token


def get_valid_refresh_token(db: Session, raw_token: str):
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
    stmt = select(refresh_tokens_table).where(
        refresh_tokens_table.c.token_hash == token_hash,
        refresh_tokens_table.c.revoked_at == None,  # noqa: E711
        refresh_tokens_table.c.expires_at > datetime.utcnow(),
    )
    return db.execute(stmt).mappings().first()


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Revokes a single refresh token (signout from one device).

    Args:
        db: Database session
        raw_token: The raw token string sent by the client

    Returns:
        bool: True if a token was found and revoked, False otherwise.
    """
    token_hash = _hash_token(raw_token)
    stmt = (
        update(refresh_tokens_table)
        .where(
            refresh_tokens_table.c.token_hash == token_hash,
            refresh_tokens_table.c.revoked_at == None,  # noqa: E711
        )
        .values(revoked_at=datetime.utcnow())
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0


def revoke_all_user_tokens(db: Session, user_id: str):
    """
    Revokes all active refresh tokens for a user (signout from all devices).

    Args:
        db: Database session
        user_id: The user's UUID
    """
    stmt = (
        update(refresh_tokens_table)
        .where(
            refresh_tokens_table.c.user_id == user_id,
            refresh_tokens_table.c.revoked_at == None,  # noqa: E711
        )
        .values(revoked_at=datetime.utcnow())
    )
    db.execute(stmt)
    db.commit()
