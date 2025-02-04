import subprocess
import os
from dotenv import load_dotenv
from paths import BASE_DIR, data_path

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")  # Sử dụng biến môi trường GitHub token

async def push_to_git(repo_path, commit_message="Tự động cập nhật data"):
    github_username = "nhathuynguyen19"
    github_repo = "Husci-Bot"
    repo_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{github_repo}.git"

    try:
        # Kiểm tra xem có thay đổi nào không
        status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("❌ Không có thay đổi nào để commit.")
            return

        # Thêm các thay đổi
        subprocess.run(["git", "-C", repo_path, "add", data_path], check=True)
        
        # Commit các thay đổi
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
        
        # Đặt URL remote
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)
        
        # Push lên branch mặc định (thay đổi thành 'main' nếu cần)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], check=True)
        
        print("✅ Đã push thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi push: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")

# Gọi hàm push_to_git
# await push_to_git(BASE_DIR)