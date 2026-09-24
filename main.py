import discord
import os
import time
import logging
import asyncio
import aiohttp

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

# Known Instagram embed mirrors, in priority order.
# These are community-run proxies and go up/down over time, so we
# health-check them at request time instead of hardcoding one.
INSTAGRAM_MIRRORS = [
    "ddinstagram.com",
    "kkinstagram.com",
    "instagramez.com",
    "eeinstagram.com",
    "instagram7.com",
    "toinstagram.com",
]

_ig_cache = {"domain": None, "checked_at": 0}
_IG_CACHE_TTL = 300  # re-check every 5 minutes


async def _check_domain(session, domain):
    """Return (domain, is_up) for a single mirror."""
    try:
        async with session.head(f"https://{domain}", allow_redirects=True) as resp:
            return domain, resp.status < 400
    except Exception as e:
        logger.warning(f"Instagram mirror {domain} failed check: {e}")
        return domain, False


async def get_working_instagram_domain():
    """Return the highest-priority Instagram mirror that's currently up.

    Checks all mirrors concurrently (so total wait time is bounded by the
    slowest single check, not the sum of all of them), then picks the
    result in INSTAGRAM_MIRRORS priority order rather than by whichever
    happened to respond first. Caches the result for _IG_CACHE_TTL seconds
    so normal message traffic doesn't trigger a network check every time.
    """
    now = time.time()
    if _ig_cache["domain"] and (now - _ig_cache["checked_at"] < _IG_CACHE_TTL):
        return _ig_cache["domain"]

    timeout = aiohttp.ClientTimeout(total=2)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        results = await asyncio.gather(
            *(_check_domain(session, d) for d in INSTAGRAM_MIRRORS)
        )

    results_by_domain = dict(results)

    for domain in INSTAGRAM_MIRRORS:
        if results_by_domain.get(domain):
            _ig_cache["domain"] = domain
            _ig_cache["checked_at"] = now
            logger.info(f"Instagram mirror check: using {domain}")
            return domain

    logger.warning("No Instagram mirrors responded; falling back to cached/default")
    return _ig_cache["domain"] or INSTAGRAM_MIRRORS[0]


async def embed(message: str):
    aliased = None
    if "twitter.com" in message and "vxtwitter" not in message and "status" in message:
        aliased = message.replace("twitter.com", "vxtwitter.com")
    elif "x.com" in message and "vxtwitter" not in message and "status" in message:
        aliased = message.replace("x.com", "vxtwitter.com")
    elif (
        "instagram.com" in message
        and not any(m in message for m in INSTAGRAM_MIRRORS)
        and ("reels" in message or "reel" in message)
    ):
        domain = await get_working_instagram_domain()
        aliased = message.replace("instagram.com", domain)
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

    aliased = await embed(message.content)
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
