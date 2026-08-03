path = 'bot/cogs/onboarding.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = '''        member = guild.get_member(self.target_user_id)
        if member:
            role_id = self.cog.config.member_role_id
            if role_id:
                role = guild.get_role(int(role_id))
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass'''

new_logic = '''        member = guild.get_member(self.target_user_id)
        if member:
            role_id = self.cog.config.member_role_id
            if not role_id:
                await interaction.followup.send("⚠️ Cảnh báo: Chưa cài đặt Member Role nên bot không thể cấp role. Dùng `/recuibot setup_roles` để cài!", ephemeral=True)
            else:
                role = guild.get_role(int(role_id))
                if not role:
                    await interaction.followup.send("⚠️ Cảnh báo: Role ID đã lưu không tồn tại (có thể role đã bị xóa). Dùng `/recuibot setup_roles` để cài lại!", ephemeral=True)
                else:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        await interaction.followup.send("⚠️ Cảnh báo: Bot không có quyền cấp Role này (Role của bot đang đứng thấp hơn Role cần cấp, hoặc bot thiếu quyền Manage Roles)!", ephemeral=True)
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Cảnh báo: Lỗi khi cấp role: {e}", ephemeral=True)
        else:
            await interaction.followup.send("⚠️ Cảnh báo: Không tìm thấy thành viên này trong server (có thể họ đã out).", ephemeral=True)'''

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated approve logic')
else:
    print('Could not find old logic')
