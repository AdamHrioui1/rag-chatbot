import jwt
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Changed to auto_error=False for custom handling

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify JWT token from Authorization header
    This uses the same ACCESS_TOKEN_SECRET as your MERN app
    """
    # If credentials is None, token wasn't provided
    if not credentials:
        logger.error("No credentials provided")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    
    # Debug: Log token info (remove in production)
    logger.info(f"Received token: {token[:20]}...")  # Log first 20 chars only
    
    try:
        # Decode token using the same secret as your MERN app
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        logger.info(f"Token decoded successfully. User ID: {payload.get('id')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )