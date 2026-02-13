"""
Clerk.dev Authentication Integration

Handles JWT verification, user session management, and tenant mapping.
"""

import os
from typing import Optional, Dict
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status


class ClerkAuth:
    """
    Clerk.dev authentication client.
    
    Verifies JWT tokens from Clerk and extracts user information.
    """
    
    def __init__(self):
        self.clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        self.clerk_publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")
        self.clerk_jwks_url = os.getenv(
            "CLERK_JWKS_URL",
            "https://api.clerk.dev/v1/jwks"
        )
        
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable is required")
        
        # Initialize JWK client for token verification
        self.jwks_client = PyJWKClient(self.clerk_jwks_url)
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify Clerk JWT token and return claims.
        
        Args:
            token: JWT token from Authorization header
            
        Returns:
            Dict with user claims (user_id, email, etc.)
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Verify and decode token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication error: {str(e)}"
            )
    
    def get_user_id(self, claims: Dict) -> str:
        """Extract user ID from JWT claims"""
        return claims.get("sub") or claims.get("user_id")
    
    def get_user_email(self, claims: Dict) -> Optional[str]:
        """Extract email from JWT claims"""
        return claims.get("email") or claims.get("email_address")
    
    def get_user_name(self, claims: Dict) -> Optional[str]:
        """Extract full name from JWT claims"""
        first_name = claims.get("first_name", "")
        last_name = claims.get("last_name", "")
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        return first_name or last_name or None


# Singleton instance
clerk_auth = ClerkAuth()
