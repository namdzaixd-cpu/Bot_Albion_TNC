import os
with open('bot/cogs/guildcheck.py', 'r', encoding='utf-8') as f: content = f.read()
if 'cog_app_command_error' not in content:
    content += '\n    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):\n        if isinstance(error, app_commands.CommandOnCooldown):\n            await interaction.response.send_message(f"⏳ Lệnh đang hồi chiêu, thử lại sau {error.retry_after:.1f} giây.", ephemeral=True)\n        else:\n            print(f"[Error] {error}")\n'
    with open('bot/cogs/guildcheck.py', 'w', encoding='utf-8') as f: f.write(content)
    print('Added error handler')
else:
    print('Error handler exists')
