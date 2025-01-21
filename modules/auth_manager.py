import base64, time
from cryptography.fernet import Fernet
from config import logger

class AuthManager:
    def __init__(self, key):
        self.fernet = Fernet(key)

    async def encrypt_password(self, password, discord_id):
        combined = f"{password}:{discord_id}"
        encrypted = self.fernet.encrypt(combined.encode())
        return base64.b64encode(encrypted).decode("utf-8")

    async def decrypt_password(self, encrypted_password, discord_id, start_time):
        # Kiểm tra nếu password không hợp lệ (None hoặc rỗng)
        if not encrypted_password:
            logger.error(f"encrypted_password không thể là None hoặc rỗng. Discord ID: {discord_id}")
            return None
        
        try:
            # Giải mã base64
            encrypted_password_base64 = base64.b64decode(encrypted_password)
            
            # Tiến hành giải mã bằng Fernet
            decrypted_combined = self.fernet.decrypt(encrypted_password_base64).decode()
            
            # Tách chuỗi thành mật khẩu và ID Discord
            password, original_discord_id = decrypted_combined.split(":")
            
            if int(original_discord_id) == discord_id:
                print(f"Đã giải mã: {time.time() - start_time:.2f} giây")
                return password
            else:
                logger.error(f"ID không khớp! ID Discord: {discord_id}, ID trong mật khẩu: {original_discord_id}")
                return None
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi trong quá trình giải mã: {e}")
            return None
