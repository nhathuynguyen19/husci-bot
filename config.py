import logging, discord

admin_id=767394443820662784

# Configure logger
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="data/bot.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

async def load_md_line_by_line(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()  # Đọc từng dòng vào danh sách
        return lines
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

