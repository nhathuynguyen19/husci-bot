import asyncio, aiohttp, lxml, time, json, os
from bs4 import BeautifulSoup
from colorama import init, Fore
from config import logger
from modules.utils.http import fetch_page, fetch_page_content, login_page
from paths import data_url

# Initialize colorama
init(autoreset=True)

class HUSCNotifications:
    def __init__(self, login_url, data_url, fixed_key, notifications_path):
        self.login_url = login_url
        self.data_url = data_url
        self.key = fixed_key
        self.notifications_path = notifications_path

    async def get_notification_first_line(self):
        try:
            with open(self.notifications_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()  # Chỉ lấy dòng đầu tiên và loại bỏ ký tự dư thừa
            return first_line
        except FileNotFoundError:
            logger.warning(f"Tệp {self.notifications_path} không tồn tại. Trả về tập hợp rỗng.")
            return set()
        except Exception as e:
            logger.error(f"Lỗi khi đọc tệp {self.sent_reminders_path}: {e}")
            return set()

    async def read_notifications(self):
        if os.path.exists(self.notifications_path):
            try:
                with open(self.notifications_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    notifications = [line.strip() for line in lines if line.strip()]
                    return notifications
            except FileNotFoundError:
                logger.warning(f"Tệp {self.notifications_path} không tồn tại. Trả về tập hợp rỗng.")
                return set()
            except Exception as e:
                logger.error(f"Lỗi khi đọc tệp {self.sent_reminders_path}: {e}")
                return set()
        else:
            logger.warning(f"File {self.notifications_path} không tồn tại.")
            return set()
    
    async def fetch_notifications(self, session):
        start_time = time.time()
        while True:
            data_response_news = await fetch_page(session, self.data_url)
            if data_response_news.status != 200:
                message = f"Không thể lấy thông báo từ {self.data_url}. Mã lỗi: {data_response_news.status}"
                logger.error(message)
                continue
            print(f"Đã lấy thông báo: {time.time() - start_time:.2f}s")
            break
        return data_response_news
    
    async def parse_notifications(self, data_response_news):
        start_time = time.time()
        soup = BeautifulSoup(await data_response_news.text(), 'lxml')
        news_list = soup.find('div', id='newsList')
        if not news_list:
            logger.error("Không tìm thấy danh sách thông báo!")
            return "Không tìm thấy danh sách thông báo!"
        notifications = [
            f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
            for link in news_list.find_all('a', href=True) if '/News/Content' in link['href']
        ][:5]
        return notifications if notifications else "Không có thông báo mới"
    
    async def check_login_infomation(self, login_id, encrypted_password, start_time=time.time()):
        if not login_id or not encrypted_password:
            logger.error("Thông tin đăng nhập không hợp lệ.")
            return "Thông tin đăng nhập không hợp lệ."
        print(f"Thông tin đăng nhập hợp lệ: {time.time() - start_time:.2f}s")

    async def fetch_data(self, session, login_id, password):
        try:
            login_message = await login_page(session, self.login_url, login_id, password)
            data_response_news = await self.fetch_notifications(session)
            notifications = await self.parse_notifications(data_response_news)
            return notifications
        except Exception as e:
            return f"Đã xảy ra lỗi: {e}"
    
    async def get_notifications(self, user_id, user_manager, auth_manager):
        start_time = time.time()
        credentials = await user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.error("Không có thông tin đăng nhập")
            return "Không có thông tin đăng nhập"
        print(f"Tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f} giây")
        login_id, encrypted_password = credentials.get("login_id"), credentials.get("password")
        await self.check_login_infomation(login_id, encrypted_password)
        password = auth_manager.decrypt_password(encrypted_password, user_id) 
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task(self.fetch_data(session, login_id, password))
            return await task
