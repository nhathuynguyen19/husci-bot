import json, os, datetime, time

class UserManager:
    def __init__(self, user_file="users.json"):
        self.user_file = user_file
        
        # Nếu file không tồn tại, tạo file mới
        if not os.path.exists(self.user_file):
            with open(self.user_file, "w", encoding="utf-8") as file:
                json.dump([], file, ensure_ascii=False, indent=4)

    async def get_user_credentials(self, user_id):
        try:
            with open(self.user_file, "r", encoding="utf-8") as file:
                users = json.load(file)
                for user in users:
                    if user["id"] == user_id:
                        return user  # Trả về tài khoản và mật khẩu
                return None  # Không tìm thấy user_id
        except FileNotFoundError:
            return None  # File không tồn tại

    async def save_user_to_file(self, user, username=None, password=None):
        user_data = {
            "name": user.name,
            "id": user.id,
            "login_id": username,
            "password": password,
        }

        try:
            with open(self.user_file, "r", encoding="utf-8") as file:
                content = file.read().strip()
                data = json.loads(content) if content else []
        except Exception as e:
            print(f"Lỗi khi đọc file: {e}")
            data = []

        # Kiểm tra nếu user đã tồn tại trong file
        if any(existing_user["id"] == user.id for existing_user in data):
            return False

        # Thêm user mới vào dữ liệu
        data.append(user_data)

        # Lưu lại dữ liệu vào file
        with open(self.user_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return True

    async def remember_request(self, user_id, user_name, command):
        # Kiểm tra xem file có tồn tại không, nếu không thì tạo mới
        if not os.path.exists("request.txt"):
            with open("request.txt", "w", encoding="utf-8") as file:
                # Tạo file trống (hoặc có thể thêm tiêu đề vào nếu cần)
                file.write("Dữ liệu request:\n")
        
        # Mở file để ghi thêm dữ liệu
        with open("request.txt", "a", encoding="utf-8") as file:
            file.write(f"User ID: {user_id}, User Name: {user_name}, Command: {command}, Time: {datetime.datetime.now()}\n")