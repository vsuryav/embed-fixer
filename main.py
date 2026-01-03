import discord
import os
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("embed-fixer")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  

bot = discord.Bot(intents=intents)

def embed(message: str):
    aliased = None
    if "twitter.com" in message and "vxtwitter" not in message and "status" in message:
        aliased = message.replace("twitter.com", "vxtwitter.com")
    elif "x.com" in message and "vxtwitter" not in message and "status" in message:
        aliased = message.replace("x.com", "vxtwitter.com")
    elif "instagram.com" in message and "kkinstagram.com" not in message and ("reels" in message or "reel" in message):
        aliased = message.replace("instagram.com", "kkinstagram.com")
    return aliased

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guilds")

@bot.event
async def on_message(message):
    # Ignore all bot messages (including our own)
    if message.author.bot:
        return
    
    # Additional safety: ignore messages that match our posting pattern
    if " shared: " in message.content:
        return

    # Check if the message is from RSC
    if message.guild and message.guild.name == "Rush Site C":
        if "x.com" in message.content or "twitter.com" in message.content:
            try:
                await message.delete()
                await message.author.send(
                    f"Hi {message.author.name}, your message comes from a bad place (`twitter`)."
                )
                logger.info(f"Deleted Twitter link from {message.author.name} in RSC and sent DM")
            except discord.Forbidden:
                logger.warning(f"Could not send DM to {message.author.name}")
                with open("embed.log", "a") as file:
                    now = time.time()
                    file.write(f"Could not send a DM to {message.author.name}.\n")
            return

    aliased = embed(message.content)

    if aliased:
        await message.channel.send(f"{message.author.display_name} shared: {aliased}")
        await message.delete()
        logger.info(f"Posted embed for {message.author.display_name} in #{message.channel.name}")
        
        with open("embed.log", "a") as file:
            now = time.time()
            file.write(f"{now}-{message.author.name}-{message.content}\n")

discord_key = os.environ.get("discord")

if discord_key is None:
    logger.error("Discord environment variable is not set")
    raise ValueError("discord environment variable is not set")

logger.info("Starting embed-fixer bot...")
bot.run(discord_key)
