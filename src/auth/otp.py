from src.auth import storage
import secrets
import hashlib


def generate_otp() -> str:
  """
  Generate a cryptographically secure random string that can be used as an OTP.

  Returns:
      str: A random string that can be used as an OTP
  """
  return str(secrets.randbelow(900_000) + 100_000)


def generate_flow_token() -> str:
  """
  Generate a cryptographically secure random string that can be used as a flow token.
  
  Returns:
    str: A random string that can be used as a flow token
  """
  return secrets.token_urlsafe(32)


def hash_otp(otp: str) -> str:
  """
  Hash the given OTP.

  Args:
      otp (str): The OTP to hash

  Returns:
      str: The hashed OTP
  """
  return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp_hash(otp: str, hashed: str) -> bool:
  """
  Verify the given OTP against the hashed OTP.

  Args:
      otp (str): The OTP to verify
      hashed (str): The hashed OTP

  Returns:
      bool: True if the OTP is valid, False otherwise
  """
  return hashlib.sha256(otp.encode()).hexdigest() == hashed
