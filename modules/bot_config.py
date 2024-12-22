import os, discord, base64
from dotenv import load_dotenv
from discord.ext import commands

class BotConfig:
    def __init__(self):
        # Load biến môi trường
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        self.fixed_key = os.getenv("FIXED_KEY")
        self.fixed_key = base64.b64decode(self.fixed_key)
        self.admin_id = os.getenv("ADMIN_ID")

        if not self.token:
            raise ValueError("Thiếu biến DISCORD_TOKEN, FIXED_KEY trong môi trường!")

    def create_bot(self, prefix="/"):
        intents = discord.Intents.default()
        intents.members = True  # Đảm bảo bot có thể thấy thành viên
        intents.message_content = True
        return commands.Bot(command_prefix=prefix, intents=intents)
