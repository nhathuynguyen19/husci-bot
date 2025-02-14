import os, discord, base64, asyncio
from dotenv import load_dotenv
from discord.ext import commands
from config import logger
<<<<<<< HEAD

class BotConfig:
    def __init__(self):
        load_dotenv()
=======
from paths import dotenv_path

class BotConfig:
    def __init__(self):
        load_dotenv(dotenv_path)
>>>>>>> e23f034 (update)
        self.token = os.getenv("DISCORD_TOKEN")
        self.fixed_key = os.getenv("FIXED_KEY")
        self.fixed_key = base64.b64decode(self.fixed_key)
        if not self.token:
            logger.error("Thiếu biến DISCORD_TOKEN, FIXED_KEY trong môi trường!")

    def create_bot(self, prefix="/"):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        return commands.Bot(command_prefix=prefix, intents=intents)
