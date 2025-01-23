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
temp_path = os.path.join(BASE_DIR, 'data', 'temp.txt')
unique_member_ids_path = os.path.join(BASE_DIR, 'data', 'unique_member_ids.json')

login_url = "https://student.husc.edu.vn/Account/Login"
data_url = [
    "https://student.husc.edu.vn/News",
    "https://student.husc.edu.vn/Message/Inbox",
    "https://student.husc.edu.vn/Statistics/HistoryOfStudying"
]
