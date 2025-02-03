import subprocess, os
from dotenv import load_dotenv
from paths import BASE_DIR, data_path

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

async def push_to_git(repo_path, commit_message="Tự động cập nhật data"):
    github_username = "nhathuynguyen19"
    github_token = token
    github_repo = "Husi-Bot"
    repo_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{github_repo}.git"

    try:
        subprocess.run(["git", "-C", repo_path, "add", data_path], check=True)
        subprocess.run(["git", "-C", repo_path, "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "-C", repo_path, "remote", "set-url", "origin", repo_url], check=True)
        subprocess.run(["git", "-C", repo_path, "push", "origin", "master"], check=True)
        print("✅ Đã push thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi push: {e}")
