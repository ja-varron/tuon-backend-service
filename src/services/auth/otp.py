import logging
import random
import string
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.config import settings
from core.security import get_password_hash, verify_password
from repositories import otp_flows, users, institutions, profiles
from schemas.auth.otp import OTPVerifyRequest

logger = logging.getLogger(__name__)

def generate_otp(db: Session, email: str, institution_name: str, user_id: str) -> str:
    """
    Generates an OTP for the given email address.
    
    Args:
        db: Database session
        email: Email address
        institution_name: Institution name submitted at signup
        user_id: User ID
        
    Returns:
        str: OTP code
    """
    # Generates a random 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))

    # Hashes the OTP
    otp_hash = get_password_hash(otp_code)

    # Sets the expiration time for the OTP
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Creates the OTP flow in the database, storing institution_name for later retrieval
    otp_flows.create_otp_flow(db, email, institution_name, otp_hash, expires_at, user_id)
    return otp_code


def verify_admin_otp(db: Session, verify_data: OTPVerifyRequest):
    """
    Verifies the OTP and finalizes the account creation.
    
    Args:
        db: Database session
        verify_data: OTP verification data
        
    Returns:
        dict: Success message
    """

    # Retrieves the OTP flow
    flow = otp_flows.get_active_otp_flow(db, verify_data.email)
    
    # Checks if the OTP flow is valid
    if not flow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP flow found or OTP expired")
        
    # Checks if the OTP has reached the maximum number of attempts
    if flow.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp_flows.invalidate_otp_flow(db, flow.otp_flow_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Max OTP attempts reached")
    
    # Checks if the OTP is valid
    if not verify_password(verify_data.otp, flow.otp_hash):
        otp_flows.increment_attempts(db, flow.otp_flow_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")
        
    # Valid OTP — retrieve institution_name that was saved at signup time
    try:
        # Invalidate OTP flow
        otp_flows.invalidate_otp_flow(db, flow.otp_flow_id)
        
        # Set email_created_at
        verified_at = datetime.utcnow()
        user = users.get_user_by_email(db, verify_data.email)
        
        # Guard: user should always exist at this point, but handle defensively
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")
        
        users.update_user_verification(db, user.user_id, verified_at)
        
        # Read institution_name directly from the stored OTP flow row
        institution_name = flow.institution_name
        
        institution_id = institutions.create_institution(db, institution_name, user.user_id)
        profiles.create_admin_profile(db, user.user_id, user.email, institution_id, institution_name)
        
        db.commit()
        return {"message": "OTP verified successfully. Admin account created."}
    except HTTPException:
        # Re-raise HTTP exceptions (e.g. the 404 above) without overriding them
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to finalize account creation for %s: %s", verify_data.email, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to finalize account creation")
