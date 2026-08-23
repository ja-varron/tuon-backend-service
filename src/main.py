from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.router import api_v1_router
from core.config import settings
from core.limiter import limiter

# ---------------------------------------------------------------------------
# Rate limiter — defined in core.limiter to avoid circular imports
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Tuon Backend Service",
    description="Authentication and authorization API for the Tuon platform.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Rate limiting middleware + 429 error handler
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# CORS
# Update ALLOWED_ORIGINS in .env before deploying to production.
# Example: ALLOWED_ORIGINS=https://your-frontend.com,https://admin.your-frontend.com
# ---------------------------------------------------------------------------
allowed_origins = [
    o.strip()
    for o in getattr(settings, "ALLOWED_ORIGINS", "").split(",")
    if o.strip()
] or ["http://localhost:3000", "http://localhost:5173"]  # safe defaults for local dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'"
    )
    return response

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}
