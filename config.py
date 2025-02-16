import logging, re, datetime
from paths import bot_log_path

admin_id=767394443820662784

class PlusSevenFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Lấy thời gian từ record và cộng thêm 7 giờ
        dt = datetime.datetime.utcfromtimestamp(record.created) + datetime.timedelta(hours=7)
        return dt.strftime(datefmt if datefmt else "%Y-%m-%d %H:%M:%S")

# Configure logger
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=bot_log_path,
    filemode="a"
)
logger = logging.getLogger(__name__)

for handler in logger.handlers:
    handler.setFormatter(PlusSevenFormatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"))

async def load_md_line_by_line(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()  # Đọc từng dòng vào danh sách
        return lines
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

async def convert_to_acronym(text):
    # Loại bỏ ký tự đặc biệt, giữ lại chữ cái, số và dấu cách
    cleaned_text = re.sub(r"[^\w\s-]", "", text)
    
    # Tách từ và loại bỏ các từ bị bỏ qua
    words = cleaned_text.split()
    
    # Lấy chữ cái đầu tiên của mỗi từ (viết hoa)
    acronym = "".join(word[0].upper() for word in words)

    for i in range(len(acronym) - 1, 0, -1):
        if acronym[i] == "-":
            acronym = acronym[:i]
    
    return acronym


