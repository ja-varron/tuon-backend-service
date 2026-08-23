# Security Hardening — Task Tracker

## Week 1: Core Security (Priority 1 + CORS)

### 1. JWT Middleware
- [x] `get_current_user` dependency in `src/core/security.py`
- [x] `require_role()` guard in `src/core/security.py`
- [x] `TokenPayload` schema already exists in `src/schemas/auth/tokens.py` ✅

### 2. Schemas
- [x] Update `src/schemas/auth/tokens.py` — added `RefreshTokenRequest` and `RefreshTokenResponse`
- [x] Update `src/schemas/auth/login.py` — added `refresh_token` field to `SigninResponse`

### 3. Refresh Token System
- [x] Add `refresh_tokens` table SQL migration → `sql/add_refresh_tokens_table.sql` (**run this in Supabase SQL Editor**)
- [x] `src/repositories/tokens.py` — CRUD for refresh tokens (with SHA-256 hashing)
- [x] `src/services/auth/tokens.py` — rotate / revoke / signout-all logic
- [x] `src/api/v1/auth.py` — `POST /token/refresh`, `POST /signout`, `POST /signout/all`
- [x] Update `src/services/auth/login.py` — also issues refresh token on signin

### 4. Hardening
- [x] `src/core/limiter.py` — shared limiter module (avoids circular import)
- [x] `src/main.py` — CORS middleware (reads `ALLOWED_ORIGINS` from `.env`)
- [x] `src/main.py` — security headers middleware (6 headers)
- [x] `src/main.py` — slowapi rate limiting + 429 handler
- [x] `src/api/v1/auth.py` — per-route limits (signup/OTP: 5/min, signin: 10/min, refresh: 20/min)
- [x] OTP lockout after `OTP_MAX_ATTEMPTS` — **was already implemented** ✅

## ⚠️ Blocked — Run SQL Migration First
- [ ] Run `sql/add_refresh_tokens_table.sql` in Supabase SQL Editor
- [ ] Restart uvicorn after migration

## Verification
- [ ] Test `GET /health` without token — should pass
- [ ] Test `POST /signin` — should now return `access_token` + `refresh_token`
- [ ] Test `POST /token/refresh` with valid refresh token — returns new access token
- [ ] Test `POST /signout` with access token + refresh token body — token revoked
- [ ] Test `POST /signout/all` — all sessions for user revoked
- [ ] Test `POST /signin` after signout — works, old refresh token invalid
