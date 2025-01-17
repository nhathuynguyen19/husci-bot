import json, os, datetime, time, asyncio
from config import logger
from modules.utils.file import load_json
from paths import users_path

class UserManager:
    def __init__(self, user_file="data/users.json"):
        self.user_file = user_file
        if not os.path.exists(self.user_file):
            with open(self.user_file, "w", encoding="utf-8") as file:
                json.dump([], file, ensure_ascii=False, indent=4)

    async def get_user_credentials(self, user_id):
        try:
            with open(self.user_file, "r", encoding="utf-8") as file:
                users = json.load(file)
                for user in users:
                    if user["id"] == user_id:
                        return user
                
                return None
        except FileNotFoundError:
            return None

    async def check_login_id(self, user_id):
        while True:
            if await self.get_user_credentials(user_id):
                print("Đã có thông tin trong file user.json")
                return
            else:
                logger.error("Không có thông tin trong file user.json.")
            await asyncio.sleep(10)

    async def save_user_to_file(self, user, username=None, password=None):
        user_data = {
            "name": user.name,
            "id": user.id,
            "login_id": username,
            "password": password,
        }
        data = load_json(users_path)
        if any(existing_user["id"] == user.id for existing_user in data):
            return False
        data.append(user_data)
        with open(users_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True

    async def remember_request(self, user_id, user_name, command):
        if not os.path.exists("data/request.txt"):
            with open("data/request.txt", "w", encoding="utf-8") as file:
                file.write("Dữ liệu request:\n")
        with open("data/request.txt", "a", encoding="utf-8") as file:
            file.write(f"User ID: {user_id}, User Name: {user_name}, Command: {command}, Time: {datetime.datetime.now()}\n")
