import time, aiohttp, asyncio
from modules.utils.config import logger
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
        try:
            # Load dữ liệu người dùng từ file
            users_data = await load_json(self.users_path)

            # Cập nhật sms cho user có id trùng với id trong result
            updated = False
            for user in users_data:
                if user["id"] == result["id"]:
                    if user.get("sms") != result["sms"]:  # Chỉ cập nhật nếu có thay đổi
                        user["sms"] = result["sms"]
                        updated = True
                    break  # Dừng vòng lặp khi đã tìm thấy người dùng

            # Lưu lại dữ liệu người dùng đã cập nhật
            if updated:
                await save_json(self.users_path, users_data)
                print(f"Dữ liệu người dùng {result['id']} đã được cập nhật.")
        except Exception as e:
            print(f"Lỗi khi xử lý kết quả: {str(e)}")

