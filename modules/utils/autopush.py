import subprocess
import os
from dotenv import load_dotenv
from paths import BASE_DIR, data_path, dotenv_path

load_dotenv(dotenv_path)
github_token = os.getenv("GITHUB_TOKEN")  # Sử dụng biến môi trường GitHub token

async def push_to_git(repo_path, commit_message="Tự động cập nhật data"):
    github_username = "nhathuynguyen19"
    github_repo = "Husci-Bot-Data"
    repo_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{github_repo}.git"

    try:
        # Bước 1: Copy thư mục data vào thư mục Husci-Bot-Data
        data_dir = os.path.join(BASE_DIR, "data")
        husci_bot_data_dir = os.path.join(os.path.dirname(BASE_DIR), "Husci-Bot-Data")

        # Nếu thư mục data đã tồn tại trong Husci-Bot-Data, xóa nó trước khi copy vào
        if os.path.exists(os.path.join(husci_bot_data_dir, "data")):
            subprocess.run(["rm", "-rf", os.path.join(husci_bot_data_dir, "data")], check=True)

        # Copy thư mục data vào Husci-Bot-Data
        subprocess.run(["cp", "-r", data_dir, husci_bot_data_dir], check=True)

        # Bước 2: Vào thư mục Husci-Bot-Data
        os.chdir(husci_bot_data_dir)
        
        # Kiểm tra xem có thay đổi nào không
        status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain", "data"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("❌ Không có thay đổi nào để commit.")
            return

        # Thêm các thay đổi 
        subprocess.run(["git", "-C", repo_path, "add", "data"], check=True)
        
        # Commit các thay đổi
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
        
        # Đặt URL remote
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)

        # Lấy branch hiện tại
        branch = subprocess.run(["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
        
        # Push lên branch mặc định (thay đổi thành 'main' nếu cần)
        subprocess.run(["git", "-C", repo_path, "push", "origin", branch], check=True)
        
        print("✅ Đã push thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi push: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")

# Gọi hàm push_to_git
# await push_to_git(BASE_DIR)