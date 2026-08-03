import os
from supabase import create_client, Client
from bot.core.config import SUPABASE_URL, SUPABASE_KEY, GUILD_ID

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class OnboardConfig:
    def __init__(self):
        self.guild_id = str(GUILD_ID)
        self.data = self._fetch_data()
        
    def _fetch_data(self):
        try:
            response = supabase.table("guild_config").select("*").eq("guild_id", self.guild_id).execute()
            if response.data:
                return response.data[0]
            else:
                # Create default entry
                default_data = {"guild_id": self.guild_id, "is_onboard_enabled": True}
                supabase.table("guild_config").insert(default_data).execute()
                return default_data
        except Exception as e:
            print(f"Error fetching supabase config: {e}")
            return {"is_onboard_enabled": True}
            
    def save(self):
        try:
            # We don't want to update guild_id
            update_data = {k: v for k, v in self.data.items() if k != "guild_id"}
            supabase.table("guild_config").update(update_data).eq("guild_id", self.guild_id).execute()
        except Exception as e:
            print(f"Error saving supabase config: {e}")

    @property
    def is_enabled(self):
        return self.data.get("is_onboard_enabled", True)
        
    @is_enabled.setter
    def is_enabled(self, value: bool):
        self.data["is_onboard_enabled"] = value
        self.save()

    @property
    def apply_channel_id(self):
        return self.data.get("apply_channel_id")
        
    @property
    def member_role_id(self):
        return self.data.get("member_role_id")
        
    @property
    def officer_role_id(self):
        return self.data.get("officer_role_id")
        
    @property
    def rules_channel_id(self):
        return self.data.get("rules_channel_id")
        
    @property
    def chat_channel_id(self):
        return self.data.get("chat_channel_id")
        
    @property
    def question_channel_id(self):
        return self.data.get("question_channel_id")
