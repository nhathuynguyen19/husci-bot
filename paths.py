import os

# Đường dẫn gốc của dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Định nghĩa các đường dẫn
sent_reminders_path = os.path.join(BASE_DIR, 'data', 'sent_reminders.txt')
reminders_path = os.path.join(BASE_DIR, 'data', 'reminders.txt')
notifications_path = os.path.join(BASE_DIR, 'data', 'notifications.txt')
users_path = os.path.join(BASE_DIR, 'data', 'users.json')
guilds_info_path = os.path.join(BASE_DIR, 'data', 'guilds_info.json')
temp_path = os.path.join(BASE_DIR, 'data', 'temp.txt')

login_url = "https://student.husc.edu.vn/Account/Login"
data_url = [
    "https://student.husc.edu.vn/News",
    "https://student.husc.edu.vn/Message/Inbox"
]
