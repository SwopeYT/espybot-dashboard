import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables to track channels
join_to_create_channels = set()
temporary_channels = {}

# Bot instance reference
_bot_instance = None

@bot.event
async def on_ready():
    """Called when bot is ready"""
    global _bot_instance
    _bot_instance = bot
    
    logging.info(f'{bot.user.name}#{bot.user.discriminator} has connected to Discord!')
    logging.info(f'ESPY Bot is in {len(bot.guilds)} guilds')
    
    # Load existing join-to-create channels (you can implement database loading here)
    logging.info(f'Loaded {len(join_to_create_channels)} join-to-create channels')
    logging.info(f'Loaded {len(temporary_channels)} temporary channels')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logging.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logging.error(f'Failed to sync commands: {e}')

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle voice state changes for temporary channels"""
    
    # User joined a join-to-create channel
    if after.channel and after.channel.id in join_to_create_channels:
        # Create temporary channel
        guild = after.channel.guild
        category = after.channel.category
        
        # Create new voice channel
        temp_channel = await guild.create_voice_channel(
            name=f"{member.display_name}'s Channel",
            category=category,
            user_limit=0,
            bitrate=64000
        )
        
        # Move user to new channel
        await member.move_to(temp_channel)
        
        # Track the temporary channel
        temporary_channels[temp_channel.id] = {
            'owner_id': member.id,
            'created_at': discord.utils.utcnow(),
            'channel': temp_channel
        }
        
        logging.info(f'Created temporary channel: {temp_channel.name} for {member.display_name}')
    
    # Check if temporary channel is now empty
    if before.channel and before.channel.id in temporary_channels:
        if len(before.channel.members) == 0:
            # Delete empty temporary channel
            channel_info = temporary_channels.pop(before.channel.id)
            await before.channel.delete(reason="Temporary channel empty")
            logging.info(f'Deleted empty temporary channel: {before.channel.name}')

@bot.tree.command(name="setup", description="Setup a join-to-create voice channel")
async def setup_join_to_create(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """Setup a voice channel as join-to-create"""
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You need 'Manage Channels' permission to use this command.", ephemeral=True)
        return
    
    join_to_create_channels.add(channel.id)
    await interaction.response.send_message(f"✅ {channel.name} is now a join-to-create channel!", ephemeral=True)
    logging.info(f'Added join-to-create channel: {channel.name} in {interaction.guild.name}')

@bot.tree.command(name="remove", description="Remove a join-to-create voice channel")
async def remove_join_to_create(interaction: discord.Interaction, channel: discord.VoiceChannel):
    """Remove a voice channel from join-to-create"""
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You need 'Manage Channels' permission to use this command.", ephemeral=True)
        return
    
    if channel.id in join_to_create_channels:
        join_to_create_channels.remove(channel.id)
        await interaction.response.send_message(f"✅ {channel.name} is no longer a join-to-create channel!", ephemeral=True)
        logging.info(f'Removed join-to-create channel: {channel.name} in {interaction.guild.name}')
    else:
        await interaction.response.send_message(f"❌ {channel.name} is not a join-to-create channel.", ephemeral=True)

@bot.tree.command(name="list", description="List all join-to-create channels")
async def list_join_to_create(interaction: discord.Interaction):
    """List all join-to-create channels in the guild"""
    guild_channels = [ch_id for ch_id in join_to_create_channels if interaction.guild.get_channel(ch_id)]
    
    if not guild_channels:
        await interaction.response.send_message("No join-to-create channels configured in this server.", ephemeral=True)
        return
    
    channel_list = []
    for ch_id in guild_channels:
        channel = interaction.guild.get_channel(ch_id)
        if channel:
            channel_list.append(f"• {channel.name}")
    
    embed = discord.Embed(
        title="Join-to-Create Channels",
        description="\n".join(channel_list),
        color=0x13b2fb
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def start_discord_bot():
    """Start the Discord bot"""
    try:
        bot_token = os.getenv('DISCORD_BOT_TOKEN')
        if not bot_token:
            logging.error("DISCORD_BOT_TOKEN not found in environment variables")
            return
        
        await bot.start(bot_token)
    except Exception as e:
        logging.error(f"Failed to start Discord bot: {e}")

async def stop_discord_bot():
    """Stop the Discord bot"""
    if bot.is_closed():
        return
    await bot.close()

def get_bot_instance():
    """Get the bot instance"""
    return _bot_instance

def add_join_to_create_channel(channel_id: int):
    """Add a channel to join-to-create list"""
    join_to_create_channels.add(channel_id)

def remove_join_to_create_channel(channel_id: int):
    """Remove a channel from join-to-create list"""
    join_to_create_channels.discard(channel_id)

def get_join_to_create_channels():
    """Get all join-to-create channels"""
    return list(join_to_create_channels)

def get_temporary_channels():
    """Get all temporary channels"""
    return dict(temporary_channels)
