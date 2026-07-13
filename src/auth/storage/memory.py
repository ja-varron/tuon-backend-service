from cachetools import TTLCache
from threading import Lock
from datetime import datetime as dt
from src.config import settings

_ttl = settings.OTP_EXPIRE_MINUTES * 60
_cache: TTLCache = TTLCache(maxsize=10_000, ttl=_ttl)
_lock = Lock()


def store_flow(token: str, data: dict) -> None:
  """
  Store a flow in the cache.

  Args:
      token (str): Token to identify the flow.
      data (dict): Data to store in the cache.
      
  Returns:
      None
  """
  with _lock:
    _cache[token] = {
      **data, "created_at": dt.utcnow()
    }


def get_flow(token: str) -> dict | None:
  """
  Get a flow from the cache.

  Args:
      token (str): Token to identify the flow.
      
  Returns:
      dict | None: Flow data if found, None otherwise.
  """
  with _lock:
    return _cache.get(token)


def update_flow(token: str, **kwargs) -> None:
  """
  Update a flow in the cache.

  Args:
      token (str): Token to identify the flow.
      kwargs: Key-value pairs to update in the flow data.
      
  Returns:
      None
  
  Raises:
      KeyError: If the flow is not found.
  """
  with _lock:
    if token in _cache:
      _cache[token].update(kwargs)
    else:
      raise KeyError("Flow not found")

      
def consume_flow(token: str) -> None:
  """
  Consume a flow in the cache.

  Args:
      token (str): Token to identify the flow.
      
  Returns:
      None
  
  Raises:
      KeyError: If the flow is not found.
  """
  with _lock:
    if token in _cache:
      _cache[token]["consumed"] = True
    else:
      raise KeyError("Flow not found")

def count_recent(email: str) -> int:
  """
  Count the number of recent flows for a given email.

  Args:
      email (str): Email address to count recent flows for.
      
  Returns:
      int: Number of recent flows for the given email.
  """
  with _lock:
    # TTL handles expiry automatically, so we only count existing entries
    return sum(1 for entry in _cache.values()
               if entry.get("email") == email and not entry.get("consumed"))
