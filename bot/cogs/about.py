import discord
from discord import app_commands
from discord.ext import commands

# ==============================================================================
# GIỚI THIỆU BOT
# ==============================================================================
WEBSITE_URL = "https://bot-albion-tnc.onrender.com/"


class AboutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="aboutme", description="Giới thiệu về TNC Manager Bot")
    async def aboutme_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ TNC Manager",
            description=(
                "Bot quản lý Guild **TNC** trong Albion Online.\n\n"
                f"🌐 [Trang giới thiệu]({WEBSITE_URL})"
            ),
            color=0x3498db,
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AboutCog(bot))
