"""
Shared rate limiter instance.

Defined here (not in main.py) to avoid circular imports when auth.py
tries to import limiter from main.py (which itself imports the auth router).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
