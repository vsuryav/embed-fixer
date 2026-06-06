import discord
import datetime
from discord.ext import commands
from llm import summarize_messages


class SummarizeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="carl", description="Summarize a user's messages from the last 5 minutes in this channel.")
    async def carl(self, ctx: discord.ApplicationContext, user: discord.Member):
        # Defer ephemerally to avoid Discord timeout
        await ctx.defer(ephemeral=True)

        # Calculate cutoff time — 5 minutes ago
        cutoff = discord.utils.utcnow() - datetime.timedelta(minutes=5)

        # Fetch messages from the last 5 minutes from this user
        collected = []
        async for msg in ctx.channel.history(limit=200, after=cutoff):
            if msg.author.id != user.id:
                continue
            if msg.author.bot:
                continue
            if not msg.content.strip():
                continue
            collected.append(msg.content.strip())

        if not collected:
            await ctx.followup.send("No messages found from that user in the last 5 minutes.", ephemeral=True)
            return

        summary = await summarize_messages(user.display_name, collected)
        await ctx.followup.send(summary, ephemeral=True)


def setup(bot):
    bot.add_cog(SummarizeCommands(bot))