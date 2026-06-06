import discord
import datetime
from discord.ext import commands
from llm import summarize_messages


class SummarizeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="carl", description="Summarize a user's most recent 10 messages in this channel.")
    async def carl(self, ctx: discord.ApplicationContext, user: discord.Member):
        # Defer ephemerally to avoid Discord timeout
        await ctx.defer(ephemeral=True)

        # Fetch the most recent 10 messages from this user
        collected = []
        async for msg in ctx.channel.history(limit=200):  # Fetch up to 200 messages
            if msg.author.id != user.id:
                continue
            if msg.author.bot:
                continue
            if not msg.content.strip():
                continue
            collected.append(msg.content.strip())
            if len(collected) == 10:  # Stop collecting after 10 messages
                break

        if not collected:
            await ctx.followup.send("No messages found from that user.", ephemeral=True)
            return

        summary = await summarize_messages(user.display_name, collected)
        await ctx.followup.send(summary, ephemeral=True)


def setup(bot):
    bot.add_cog(SummarizeCommands(bot))
