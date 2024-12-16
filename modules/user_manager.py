import json, os, datetime

class UserManager:
    def __init__(self, user_file="users.json"):
        self.user_file = user_file

    def get_user_credentials(self, user_id):
        try:
            with open(self.user_file, "r", encoding="utf-8") as file:
                users = json.load(file)
                for user in users:
                    if user["id"] == user_id:
                        return user  # Trả về tài khoản và mật khẩu
                return None  # Không tìm thấy user_id
        except FileNotFoundError:
            return None  # File không tồn tại

    def save_user_to_file(self, user, username=None, password=None):
        user_data = {
            "name": user.name,
            "id": user.id,
            "login_id": username,
            "password": password,
        }

        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, "r", encoding="utf-8") as file:
                    content = file.read().strip()
                    data = json.loads(content) if content else []
            else:
                data = []
        except Exception as e:
            print(f"Lỗi khi đọc file: {e}")
            data = []

        if any(existing_user["id"] == user.id for existing_user in data):
            return False

        data.append(user_data)

        with open(self.user_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return True

    async def remember_request(user_id, user_name, command):
        with open("request.txt", "a", encoding="utf-8") as file:
            file.write(f"User ID: {user_id}, User Name: {user_name}, Command: {command}, Time: {datetime.datetime.now()}\n")