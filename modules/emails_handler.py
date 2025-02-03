import time, aiohttp, asyncio
from config import logger
from bs4 import BeautifulSoup
from paths import login_url, data_url, BASE_DIR
from modules.utils.file import save_txt, load_json, save_json
from modules.utils.http import fetch_data
from modules.utils.autopush import push_to_git

class EmailsHandler:
    def __init__(self, auth_manager, bot, users_path):
        self.auth_manager = auth_manager
        self.bot = bot
        self.users_path = users_path

    async def process_result(self, latest_email, user_id_spec, bot):
        try:
            users_data = await load_json(self.users_path)
            updated = False
            for user in users_data:
                if user['id'] == user_id_spec:
                    old_message = user["sms"]
    
                    if old_message is None or old_message == "" or old_message != latest_email:
                        user["sms"] = latest_email
                        updated = True
                        user_obj = await bot.fetch_user(int(user['id']))
                        if user_obj:
                            if old_message is None or old_message == "":
                                print(f"Tin nhắn rỗng, đã lấy tin nhắn mới nhất: {user_id_spec}")
                            else:
                                await user_obj.send(f"**Tin nhắn mới**:\n{latest_email}")
                                print(f"Tin nhắn mới đã gửi đến {user_id_spec}: {latest_email}")
                        else:
                            print(f"Không tìm thấy người dùng với ID: {user_id_spec}")

                            
            if updated:
                await save_json(self.users_path, users_data)
                print(f"Dữ liệu người dùng {user_id_spec} đã được cập nhật.")
                await push_to_git(BASE_DIR, "Update SMS")
        except Exception as e:
            print(f"Lỗi khi xử lý kết quả: {str(e)}")

