# File: app/security/authentication.py
# Author: MCP Development Core
# Description: Handles Firebase Authentication and token verification.

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials
import firebase_admin
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Firebase Admin SDK Initialization ---

# This is a critical security step. We will get the path to our credentials
# from an environment variable rather than hardcoding it.
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

if not cred_path:
    raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable not set.")

# Initialize the app, but only if it hasn't been initialized already.
# This prevents errors during hot-reloading in development.
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Reusable dependency using a class for organization
bearer_scheme = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    A FastAPI dependency that verifies the Firebase ID token from the
    Authorization header and returns the decoded user data.

    If the token is invalid or expired, it raises an HTTPException.
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing",
        )
    
    try:
        # The core verification step
        decoded_token = auth.verify_id_token(creds.credentials)
        return decoded_token
    except Exception as e:
        # This catches various Firebase exceptions (expired, revoked, invalid signature, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
        )