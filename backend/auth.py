import os
import httpx
from fastapi import HTTPException, Depends, Cookie
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OAuth configuration
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET") 
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"

security = HTTPBearer()

class DiscordAuth:
    def __init__(self):
        self.client_id = DISCORD_CLIENT_ID
        self.client_secret = DISCORD_CLIENT_SECRET
        self.redirect_uri = DISCORD_REDIRECT_URI
        
    def get_auth_url(self, state: str = None) -> str:
        """Generate Discord OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "identify guilds",
        }
        if state:
            params["state"] = state
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{DISCORD_OAUTH_URL}?{query_string}"
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(DISCORD_TOKEN_URL, data=data, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Discord API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            return response.json()
    
    async def get_user_guilds(self, access_token: str) -> list:
        """Get user's Discord guilds"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user guilds")
            return response.json()

def create_jwt_token(user_data: Dict[str, Any], access_token: str) -> str:
    """Create JWT token for user session"""
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "discriminator": user_data.get("discriminator", "0"),
        "avatar": user_data["avatar"],
        "access_token": access_token,
        "exp": int(time.time()) + 3600 * 24 * 7,  # 7 days
        "iat": int(time.time())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(auth_token: Optional[str] = Cookie(None)):
    """Dependency to get current authenticated user"""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = verify_jwt_token(auth_token)
        return {
            "id": payload["user_id"],
            "username": payload["username"],
            "discriminator": payload.get("discriminator", "0"),
            "avatar": f"https://cdn.discordapp.com/avatars/{payload['user_id']}/{payload['avatar']}.png" if payload["avatar"] else "https://cdn.discordapp.com/embed/avatars/0.png",
            "access_token": payload["access_token"]
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Create auth instance
discord_auth = DiscordAuth()
