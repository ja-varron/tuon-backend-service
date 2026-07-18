from fastapi import APIRouter, HTTPException, Request
from slowapi.util import get_remote_address
from ..schemas import SendOTPRequest
from ..auth.storage import consume_flow
from ..schemas import VerifyOTPRequest
from ..config import settings
from ..auth.storage import count_recent, store_flow, get_flow
from slowapi import Limiter
from datetime import datetime, timedelta
from ..auth.otp import generate_otp, generate_flow_token, hash_otp
from ..auth.mailer import send_email

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)

@router.post("/send-otp")
@limiter.limit("10/minute")
def send_otp(request: Request, body: SendOTPRequest):
  """
  Sends a one-time password to the specified email address.
  
  Args:
    request (Request): The HTTP request.
    email (str): The email address to send the OTP to.
    
  Returns:
    dict: A response indicating the status of the OTP.
  """
  if count_recent(body.email) >= settings.OTP_RATE_LIMIT_PER_HOUR:
    raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

  otp = generate_otp()
  flow_token = generate_flow_token()
  expires_at = datetime.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

  store_flow(flow_token, {
    "email": body.email,
    "otp_hash": hash_otp(otp),
    "expires_at": expires_at,
    "attempts": 0,
    "consumed": False
  })

  send_email(body.email, otp)

  return {
    "flow_token": flow_token
  }


@router.post("/verify-otp")
@limiter.limit("10/minute")
def verify_otp(request: Request, body: VerifyOTPRequest):
  """
  Verifies the OTP code.
  
  Args:
    request (Request): The HTTP request.
    body (VerifyOTPRequest): The OTP code and flow token to verify.
    
  Returns:
    dict: A response indicating the status of the OTP verification.
  """
  
  flow = get_flow(body.flow_token)
  # Check if flow is not found or already consumed
  if not flow or flow['consumed']:
    raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
  
  # Check if flow attempts are more than the allowed attempts
  if flow['attempts'] >= settings.OTP_MAX_ATTEMPTS:
    raise HTTPException(status_code=400, detail="Too many attempts. Please try again later.")
  
  # Check if the flow is expired at the current time
  if flow['expires_at'] < datetime.now():
    raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    
  # Check if the OTP is incorrect
  if hash_otp(body.otp_code) != flow['otp_hash']:
    flow['attempts'] += 1
    store_flow(body.flow_token, flow)
    raise HTTPException(status_code=400, detail="Invalid OTP.")
    
  consume_flow(body.flow_token)
  
  return {
    "status": "success"
  }

  
  
  
    