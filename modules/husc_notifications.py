import asyncio, aiohttp, lxml, time, json, os
from bs4 import BeautifulSoup
from colorama import init, Fore
from config import logger

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

    async def fetch_page(self, session, url, timeout=20):
        start_time = time.time()
        response = await session.get(url, timeout=timeout)
        print(f"Đã truy cập {Fore.LIGHTBLUE_EX}{url}{Fore.WHITE}:{time.time() - start_time:.2f}s")
        return response
    
    async def fetch_page_content(self, session, url, timeout=20):
        response = await self.fetch_page(session, url, timeout)
        start_time = time.time()
        content = await response.text()
        print(f"Lấy nội dung trang: {time.time() - start_time:.2f}s")
        return content
    
    async def login(self, session, login_url, login_id, password):
        page_content = await self.fetch_page_content(session, login_url)
        start_time = time.time()
        soup = BeautifulSoup(page_content, 'lxml')
        token = soup.find('input', {'name': '__RequestVerificationToken'})
        print(f"Lấy Token xác thực: {time.time() - start_time:.2f}s")
        if not token:
            message = "Không tìm thấy token xác thực!"
            logger.error(message)
            return message
        login_data = {
            "loginID": login_id,
            "password": password,
            "__RequestVerificationToken": token['value']
        }
        start_time = time.time()
        login_response = await session.post(login_url, data=login_data, timeout=20)
        if login_response.status != 200:
            message = f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"
            logger.error(message)
            return message
        print(f"Đã đăng nhập: {time.time() - start_time:.2f}s")
        return None
    
    async def fetch_notifications(self, session):
        start_time = time.time()
        while True:
            data_response_news = await self.fetch_page(session, self.data_url)
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
        return notifications if notifications else "Không có thông báo mới."

    async def is_login_successful(self, response):
        content = await response.text()
        soup = BeautifulSoup(content, 'lxml')
        error = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')
        if error:
            logger.error("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
            return False
        print("Đăng nhập thành công!")
        return True
    
    async def check_login_id(self, user_id, user_manager):
        while True:
            if await user_manager.get_user_credentials(user_id):
                print("Đã có thông tin trong file user.json")
                return
            else:
                logger.error("Không có thông tin trong file user.json.")
            await asyncio.sleep(10)
    
    async def check_login_infomation(self, login_id, encrypted_password, start_time):
        if not login_id or not encrypted_password:
            logger.error("Thông tin đăng nhập không hợp lệ.")
            return "Thông tin đăng nhập không hợp lệ."
        print(f"Thông tin đăng nhập hợp lệ: {time.time() - start_time:.2f}s")
    
    async def get_notifications(self, user_id, user_manager, auth_manager):
        start_time = time.time()
        credentials = await user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.error("Không có thông tin đăng nhập.")
            return "Không có thông tin đăng nhập"
        print(f"Tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f} giây")
        start_time = time.time()
        login_id, encrypted_password = credentials.get("login_id"), credentials.get("password")
        await self.check_login_infomation(login_id, encrypted_password, start_time)
        start_time = time.time()
        password = auth_manager.decrypt_password(encrypted_password, user_id, start_time) 
        async def fetch_data(session):
            try:
                login_message = await self.login(session, self.login_url, login_id, password)
                data_response_news = await self.fetch_notifications(session)
                notifications = await self.parse_notifications(data_response_news)
                return notifications
            except Exception as e:
                return f"Đã xảy ra lỗi: {e}"
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task(fetch_data(session))
            return await task
