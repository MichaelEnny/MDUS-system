"""
Authentication endpoints (simplified for demo)
"""

from fastapi import APIRouter

router = APIRouter()

@router.post("/auth/login")
async def login():
    """Simplified login endpoint"""
    # In real implementation, would handle JWT authentication
    return {
        "access_token": "demo_token",
        "token_type": "bearer",
        "user_id": 1
    }

@router.post("/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logged out successfully"}