import os, discord
from dotenv import load_dotenv
from discord.ext import commands

class BotConfig:
    def __init__(self):
        # Load biến môi trường
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")

        if not self.token:
            raise ValueError("Thiếu biến DISCORD_TOKEN, FIXED_KEY trong môi trường!")

    def create_bot(self, prefix="/"):
        intents = discord.Intents.default()
        intents.message_content = True
        return commands.Bot(command_prefix=prefix, intents=intents)
