import discord
from discord import app_commands
from discord.ext import commands

# ==============================================================================
# GIỚI THIỆU BOT
# ==============================================================================
WEBSITE_URL = "https://bot-albion-tnc.onrender.com/"

FEATURE_FIELDS = [
    (
        "💎 Siphoned Points",
        "`/spupdate` (cập nhật log siphoned)\n"
        "`/spcheck` (xem bảng xếp hạng)\n"
        "`!addsp` (cộng điểm tay — Officer)\n"
        "`!removesp` (trừ điểm tay — Officer)\n"
        "`!removesprole` (xóa thành viên khỏi bảng — Officer)\n"
        "`!resetsp` (reset toàn bộ bảng — Officer)",
    ),
    (
        "⚔️ Massing",
        "`/massing` (tạo party PVP/PVE)\n"
        "`/masstemplatelist` (xem danh sách template)\n"
        "`/masstemplatedelete` (xóa template — Officer)",
    ),
    (
        "🛡️ GuildCheck",
        "`/registertnc` (đăng ký IGN Albion)\n"
        "`/registerfor` (đăng ký hộ member — Officer)\n"
        "`/myign` (xem IGN đã đăng ký)\n"
        "`/guildconfig` (cấu hình GuildCheck — Officer)\n"
        "`/guildcheck` (check tay rời guild — Officer)\n"
        "`/unresolved` (xem danh sách chưa xác định — Officer)",
    ),
    (
        "🔊 Alo (TTS)",
        "`/alojoin` (bot vào voice)\n"
        "`/aloleave` (bot rời voice)\n"
        "`/alonametoggle` (bật/tắt đọc tên người gửi)\n"
        "`/alo` (gửi TTS vào voice chỉ định)\n"
        "`/aloconfig` (cấu hình auto-rejoin — Officer)\n"
        "`/alomute` (tắt tiếng tạm thời)\n"
        "`/alounmute` (bật tiếng lại)",
    ),
    (
        "💰 Core-Bank",
        "`/coresetup` (cài đặt kênh — Officer)\n"
        "`/coreadd` (thêm emoji core — Officer)\n"
        "`/coreremove` (xóa emoji core — Officer)\n"
        "`/coreautoreact` (bật/tắt auto-react — Officer)\n"
        "`/corelist` (xem danh sách core)",
    ),
]


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
        for name, value in FEATURE_FIELDS:
            embed.add_field(name=name, value=value, inline=False)
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AboutCog(bot))
