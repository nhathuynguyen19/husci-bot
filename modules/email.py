
import time, aiohttp, asyncio
from config import logger
from bs4 import BeautifulSoup
from paths import login_url, data_url, temp_path
from modules.utils.file import save_txt


class Email:
    def __init__(self, data_url, login_url):
        self.data_url = data_url
        self.login_url = login_url

    async def fetch_data(self, session, login_id, password):
        try:
            page = await session.get('https://student.husc.edu.vn/Account/Login')
            html = BeautifulSoup(await page.text(), 'html.parser')
            token = html.find('input', {'name': '__RequestVerificationToken'})['value']
            login_data = {
                "loginID": login_id,
                "password": password,
                "__RequestVerificationToken": token
            }
            read_page = await session.post('https://student.husc.edu.vn/Account/Login', data=login_data)
            read_page = await session.post('https://student.husc.edu.vn/Message/Inbox', data=login_data)
            html = BeautifulSoup(await read_page.text(), 'html.parser')
            emails_list = html.find('form', id='__formMessageList')
            if not emails_list:
                logger.error("Không tìm thấy danh sách thông báo!")
            emails = [
                f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                for link in emails_list.find_all('a', href=True) if '/Message/Details' in link['href']
            ][:5]
            return emails[0]
        except Exception as e:
            return f"Đã xảy ra lỗi: {e}"