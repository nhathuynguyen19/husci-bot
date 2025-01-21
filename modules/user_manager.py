import json, os, datetime, time, asyncio, pytz
from modules.utils.config import logger
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
                    if user.get("id") == user_id:
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

    async def save_user_to_file_when_login(self, user, username=None, password=None):
        if not username or not password:
            raise ValueError("Username and password must be provided.")
        
        user_data = {
            "name": user.name,
            "id": user.id,
            "login_id": username,
            "password": password,
            "sms": ""
        }

        try:
            data = await load_json(users_path)
        except (FileNotFoundError, json.JSONDecodeError):
            data = [] 

        if any(existing_user["id"] == user.id for existing_user in data):
            return False

        data.append(user_data)
        
        try:
            with open(users_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            raise IOError(f"Error saving user data: {e}")
        
        return True

    async def remember_request(self, user_id, user_name, command):
        # Định nghĩa múi giờ (Ví dụ: Asia/Ho_Chi_Minh cho Việt Nam)
        timezone = pytz.timezone("Asia/Ho_Chi_Minh")
        current_time = datetime.datetime.now(timezone)
        
        # Ghi dữ liệu vào file với thời gian đúng múi giờ
        with open("data/request.txt", "a", encoding="utf-8") as file:
            file.write(f"User ID: {user_id}, User Name: {user_name}, Command: {command}, Time: {current_time}\n")

