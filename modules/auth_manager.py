from cryptography.fernet import Fernet
import base64

class AuthManager:
    def __init__(self, key):
        self.fernet = Fernet(key)

    def encrypt_password(self, password, discord_id):
        combined = f"{password}:{discord_id}"
        encrypted = self.fernet.encrypt(combined.encode())
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_password(self, encrypted_password, discord_id):
        # Giải mã base64 trước
        encrypted_password_base64 = base64.b64decode(encrypted_password)
        print("Giải mã thành công.")
        
        # Tiến hành giải mã bằng Fernet
        decrypted_combined = self.fernet.decrypt(encrypted_password_base64).decode()
        
        # Tách chuỗi thành mật khẩu và ID Discord
        password, original_discord_id = decrypted_combined.split(":")
        if int(original_discord_id) == discord_id:
            return password
        else:
            print("ID không khớp!")
