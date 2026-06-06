import discord
from discord.ext import commands
from llm import summarize_messages


class SummarizeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="carl", description="Summarize a user's last 10 messages in this channel.")
    async def carl(self, ctx: discord.ApplicationContext, user: discord.Member):
        # Check for "boys" role
        role_names = [role.name for role in ctx.author.roles]
        if "boys" not in role_names:
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        # Defer ephemerally to avoid Discord timeout
        await ctx.defer(ephemeral=True)

        # Fetch last 10 messages from this user in this channel
        collected = []
        async for msg in ctx.channel.history(limit=200):
            if msg.author.id != user.id:
                continue
            if msg.author.bot:
                continue
            if not msg.content.strip():
                continue
            collected.append(msg.content.strip())
            if len(collected) >= 10:
                break

        if not collected:
            await ctx.followup.send("No messages found for that user in this channel.", ephemeral=True)
            return

        summary = await summarize_messages(user.display_name, collected)
        await ctx.followup.send(summary, ephemeral=True)


def setup(bot):
    bot.add_cog(SummarizeCommands(bot))