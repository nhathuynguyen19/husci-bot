import os

# Đường dẫn gốc của dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.sep)

# Định nghĩa các đường dẫn
sent_reminders_path = os.path.join(BASE_DIR, 'data', 'sent_reminders.txt')
reminders_path = os.path.join(BASE_DIR, 'data', 'reminders.txt')
notifications_path = os.path.join(BASE_DIR, 'data', 'notifications.txt')
users_path = os.path.join(BASE_DIR, 'data', 'users.json')
guilds_info_path = os.path.join(BASE_DIR, 'data', 'guilds_info.json')
unique_member_ids_path = os.path.join(BASE_DIR, 'data', 'unique_member_ids.json')
bot_log_path = os.path.join(BASE_DIR, 'data', 'bot.log')
request_path = os.path.join(BASE_DIR, 'data', 'request.txt')
data_path = os.path.join(BASE_DIR, 'data')

def path_creator(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Tạo file rỗng nếu chưa tồn tại
    if not os.path.exists(path):
        open(path, 'w').close()

login_url = "https://student.husc.edu.vn/Account/Login"
data_url = [
    "https://student.husc.edu.vn/News",
    "https://student.husc.edu.vn/Message/Inbox",
    "https://student.husc.edu.vn/Statistics/HistoryOfStudying",
    "https://student.husc.edu.vn/TimeTable/Week"
]
