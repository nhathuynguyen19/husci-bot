from bs4 import BeautifulSoup
import requests
import data, asyncio
from modules.utils.file import save_txt
from paths import temp_path
from config import logger

login_id = '23T1080025'
password = '16082005159487!Hh'

with requests.Session() as session:
    page = session.get('https://student.husc.edu.vn/Account/Login')
    html = BeautifulSoup(page.content, 'html.parser')
    token = html.find('input', {'name': '__RequestVerificationToken'})['value']
    login_data = {
        "loginID": login_id,
        "password": password,
        "__RequestVerificationToken": token
    }
    read_page = session.post('https://student.husc.edu.vn/Account/Login', login_data)
    read_page = session.post('https://student.husc.edu.vn/Message/Inbox', login_data)

    html = BeautifulSoup(read_page.content, 'html.parser')
    emails_list = html.find('form', id='__formMessageList')
    if not emails_list:
        logger.error("Không tìm thấy danh sách thông báo!")
    emails_list = [
        f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
        for link in emails_list.find_all('a', href=True) if '/Message/Details' in link['href']
    ][:1]
    print(emails_list)