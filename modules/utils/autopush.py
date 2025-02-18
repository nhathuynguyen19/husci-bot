import asyncio
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
        # Đường dẫn đến thư mục Husci-Bot-Data
        husci_bot_data_dir = os.path.join(os.path.dirname(BASE_DIR), "Husci-Bot-Data")
        
        # Bước 1: Copy thư mục data vào thư mục Husci-Bot-Data
        data_dir = os.path.join(BASE_DIR, "data")
        if os.path.exists(os.path.join(husci_bot_data_dir, "data")):
            await run_command(["rm", "-rf", os.path.join(husci_bot_data_dir, "data")])

        await run_command(["cp", "-r", data_dir, husci_bot_data_dir])

        # Bước 2: Vào thư mục Husci-Bot-Data
        os.chdir(husci_bot_data_dir)

        # Kiểm tra xem có quá trình merge chưa hoàn tất
        status_result = await run_command(["git", "status", "--porcelain"], capture=True)
        if "MERGE_HEAD" in status_result:
            print("⚠️ Merge chưa hoàn tất, vui lòng hoàn tất merge trước.")
            return

        # Kiểm tra nếu có thay đổi trong bot.log
        status_result = await run_command(["git", "status", "--porcelain"], capture=True)
        if "data/bot.log" in status_result:
            print("⚠️ Tệp bot.log có thay đổi, commit hoặc stash trước khi tiếp tục.")
            # Commit các thay đổi trong bot.log
            await run_command(["git", "add", "data/bot.log"])
            await run_command(["git", "commit", "-m", "Lưu các thay đổi trong bot.log"])

        # Bước 3: Cấu hình git để sử dụng merge khi pull
        await run_command(["git", "config", "pull.rebase", "false"])

        # Kéo các thay đổi từ remote với merge và cho phép hợp nhất các lịch sử không liên quan
        await run_command(["git", "pull", "origin", "master", "--allow-unrelated-histories"])

        # Kiểm tra xem có thay đổi nào không
        status_result = await run_command(["git", "status", "--porcelain", "data"], capture=True)
        if not status_result.strip():
            print("❌ Không có thay đổi nào để commit.")
            return

        # Thêm thay đổi
        await run_command(["git", "add", "data"])

        # Commit thay đổi
        await run_command(["git", "commit", "-m", commit_message])

        # Đặt lại URL remote cho đúng
        await run_command(["git", "remote", "set-url", "origin", repo_url])

        # Lấy tên branch hiện tại
        branch = await run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True)

        # Push lên branch của repo Husci-Bot-Data
        await run_command(["git", "push", "origin", branch])

        print("✅ Đã push thành công vào Husci-Bot-Data!")
    except Exception as e:
        print(f"❌ Lỗi khi push: {e}")


async def run_command(command, capture=False):
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if capture:
        return stdout.decode().strip()
    if process.returncode != 0:
        raise Exception(f"Command {' '.join(command)} failed with error: {stderr.decode()}")
    
# Gọi hàm push_to_git
# await push_to_git(BASE_DIR)
