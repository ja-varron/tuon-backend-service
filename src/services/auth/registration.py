import random
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from schemas.auth.registration import AdminSignupRequest
from repositories import users
from services.auth.otp import generate_otp
from core.security import get_password_hash
from services import message

def register_admin(db: Session, signup_data: AdminSignupRequest):
    """
    Registers a new admin user.
    
    Args:
        db: Database session
        signup_data: Signup data
        
    Returns:
        dict: Success message
    """
    
    # Fetches user from the database
    existing_user = users.get_user_by_email(db, signup_data.email)
    
    # Checks if the email already exists
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    # Hashes the password
    hashed_password = get_password_hash(signup_data.password)
    
    # Creates a user record and returns the user_id for the response
    user_id = users.create_user(db, signup_data.email, hashed_password)
    
    # Generates a short-lived OTP, saving institution_name for retrieval at verification
    otp = generate_otp(db, signup_data.email, signup_data.institution_name, str(user_id))
    
    # Emails the user with OTP
    message.send_otp_email(signup_data.email, otp)
    
    # Returns success message
    return {"message": "OTP sent successfully to email", "user_id": str(user_id)}
