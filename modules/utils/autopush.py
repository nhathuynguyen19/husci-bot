import subprocess
import os
from dotenv import load_dotenv
<<<<<<< HEAD
from paths import BASE_DIR, data_path

load_dotenv()
=======
from paths import BASE_DIR, data_path, dotenv_path

load_dotenv(dotenv_path)
>>>>>>> e23f034 (update)
github_token = os.getenv("GITHUB_TOKEN")  # Sử dụng biến môi trường GitHub token

async def push_to_git(repo_path, commit_message="Tự động cập nhật data"):
    github_username = "nhathuynguyen19"
<<<<<<< HEAD
    github_repo = "Husci-Bot"
=======
    github_repo = "Husci-data"
>>>>>>> e23f034 (update)
    repo_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{github_repo}.git"

    try:
        # Kiểm tra xem có thay đổi nào không
<<<<<<< HEAD
        status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain"], capture_output=True, text=True)
=======
        status_result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain", "data"], capture_output=True, text=True)
>>>>>>> e23f034 (update)
        if not status_result.stdout.strip():
            print("❌ Không có thay đổi nào để commit.")
            return

        # Thêm các thay đổi 
<<<<<<< HEAD
        subprocess.run(["git", "-C", repo_path, "add", data_path], check=True)
=======
        subprocess.run(["git", "-C", repo_path, "add", "data"], check=True)
>>>>>>> e23f034 (update)
        
        # Commit các thay đổi
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
        
        # Đặt URL remote
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)
<<<<<<< HEAD
        
        # Push lên branch mặc định (thay đổi thành 'main' nếu cần)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], check=True)
=======

        # Lấy branch hiện tại
        branch = subprocess.run(["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
        
        # Push lên branch mặc định (thay đổi thành 'main' nếu cần)
        subprocess.run(["git", "-C", repo_path, "push", "origin", branch], check=True)
>>>>>>> e23f034 (update)
        
        print("✅ Đã push thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi push: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")

# Gọi hàm push_to_git
# await push_to_git(BASE_DIR)