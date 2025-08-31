from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import logging
from datetime import datetime

# Import Discord bot
from discord_bot import start_discord_bot, stop_discord_bot, get_bot_instance
from auth import discord_auth, get_current_user, create_jwt_token
from setup_commands import SetupCommands, ConfigCommands, remove_command, list_command, interface_command

ROOT_DIR = Path(__file__).parent
load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Discord Voice Channel Bot", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    client_name: str
    timestamp: str

class StatusCheckCreate(BaseModel):
    client_name: str

class BotStatus(BaseModel):
    is_online: bool
    guilds_count: int
    user_count: int
    temp_channels_count: int
    join_to_create_channels: List[dict]

class ChannelConfig(BaseModel):
    channel_id: int
    channel_name: str
    guild_id: int

class ChannelLog(BaseModel):
    action: str
    channel_id: int
    channel_name: str
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    timestamp: str

# Discord OAuth Routes
@api_router.get("/auth/login")
async def discord_login():
    """Redirect to Discord OAuth"""
    auth_url = discord_auth.get_auth_url()
    return {"auth_url": auth_url}

@api_router.get("/auth/callback")
async def discord_callback(code: str, response: Response):
    """Handle Discord OAuth callback"""
    try:
        # Exchange code for access token
        token_data = await discord_auth.exchange_code(code)
        access_token = token_data["access_token"]
        
        # Get user information
        user_info = await discord_auth.get_user_info(access_token)
        
        # Create JWT token
        jwt_token = create_jwt_token(user_info, access_token)
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="auth_token",
            value=jwt_token,
            max_age=3600 * 24 * 7,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return RedirectResponse(url="/dashboard", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@api_router.get("/auth/user")
async def get_auth_user(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user

@api_router.post("/auth/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}

# Bot status endpoint
@api_router.get("/bot/status")
async def bot_status(current_user: dict = Depends(get_current_user)):
    """Get bot status - requires authentication"""
    try:
        bot_instance = get_bot_instance()
        if not bot_instance:
            return {"status": "offline", "guilds_count": 0, "user_count": 0}
        
        status = {
            "status": "online" if bot_instance.is_ready() else "offline",
            "guilds_count": len(bot_instance.guilds),
            "user_count": sum(guild.member_count for guild in bot_instance.guilds),
            "username": bot_instance.user.name if bot_instance.user else "EspyBot",
            "avatar": str(bot_instance.user.avatar.url) if bot_instance.user and bot_instance.user.avatar else None
        }
        return status
    except Exception as e:
        logging.error(f"Error getting bot status: {e}")
        return {"status": "error", "message": str(e)}

@api_router.get("/bot/guilds")
async def bot_guilds(current_user: dict = Depends(get_current_user)):
    """Get bot guilds with proper server icons"""
    try:
        bot_instance = get_bot_instance()
        if not bot_instance:
            return []
        
        guilds_data = []
        for guild in bot_instance.guilds:
            guild_data = {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "icon": guild.icon.url if guild.icon else None,
                "owner": guild.owner_id == int(current_user["id"]),
                "permissions": guild.me.guild_permissions.value
            }
            guilds_data.append(guild_data)
        
        return guilds_data
    except Exception as e:
        logging.error(f"Error getting bot guilds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
