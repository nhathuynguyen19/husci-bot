
import time, aiohttp, asyncio
from config import logger
from bs4 import BeautifulSoup
from paths import login_url, data_url, temp_path
from modules.utils.file import save_txt, load_json, save_json
from modules.utils.http import fetch_data

class EmailsHandler:
    def __init__(self, auth_manager, bot, users_path):
        self.auth_manager = auth_manager
        self.bot = bot
        self.users_path = users_path

    async def process_result(self, result):
        users_data = await load_json(self.users_path)

        # Cập nhật sms cho user có id trùng với id trong result
        for user in users_data:
            if user["id"] == result["id"]:
                user["sms"] = result["sms"]  # Chỉ cập nhật sms
                break

        await save_json(self.users_path, users_data)

