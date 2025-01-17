import aiohttp, time
from bs4 import BeautifulSoup
from config import logger
from modules.utils.file import save_txt
from paths import temp_path

async def is_login_successful(response):
    content = await response.text()
    soup = BeautifulSoup(content, 'lxml')
    error = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')
    if error:
        logger.error("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
        return False
    print("Đăng nhập thành công!")
    return True

async def fetch_page(session, url, timeout=20):
    start_time = time.time()
    response = await session.get(url, timeout=timeout)
    print(f"Fetched {url} in {time.time() - start_time:.2f}s")
    return response

async def fetch_page_content(session, url, timeout=20):
    response = await fetch_page(session, url, timeout)
    start_time = time.time()
    content = await response.text()
    print(f"Lấy nội dung trang: {time.time() - start_time:.2f}s")
    return content 

async def login_page(session, login_url, login_id, password):
    page_content = await fetch_page_content(session, login_url)
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
