import jwt
from fastapi import HTTPException, Request
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def verify_token_manual(request: Request):
    """
    Manually extract and verify JWT token from Authorization header
    """
    # Get the Authorization header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        logger.error("No Authorization header found")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    # Extract token (remove "Bearer " prefix if present)
    token = auth_header
    if token.startswith('Bearer '):
        token = token[7:]  # Remove "Bearer " prefix
    
    if not token:
        logger.error("No token found in Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    logger.info(f"Extracted token: {token[:20]}...")
    
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        logger.info(f"Token decoded successfully. Payload: {payload}")
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