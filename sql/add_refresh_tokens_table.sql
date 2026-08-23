-- Migration: Add refresh_tokens table
-- Run this in your Supabase SQL Editor (or psql).
-- This creates the table that stores hashed refresh tokens for the token rotation flow.

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Store only the SHA-256 hash of the raw token, never the token itself.
    -- The raw token is returned to the client once and never stored.
    token_hash      TEXT NOT NULL UNIQUE,

    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ DEFAULT NULL,   -- NULL = still valid
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lookup by user (e.g. "revoke all sessions for user")
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
    ON refresh_tokens (user_id);

-- Index for fast lookup by hash (e.g. validate incoming refresh token)
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
    ON refresh_tokens (token_hash);
