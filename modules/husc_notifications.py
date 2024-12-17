import asyncio, aiohttp, lxml, time
from bs4 import BeautifulSoup

class HUSCNotifications:
    def __init__(self, login_url, data_url, fixed_key):
        self.login_url = login_url
        self.data_url = data_url
        self.key = fixed_key

    async def is_login_successful(self, response):
        content = await response.text()
        soup = BeautifulSoup(content, 'lxml')
        error = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')
        if error:
            print("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
            return False
        print("Đăng nhập thành công!")
        return True
    
    # Hàm kiểm tra thông tin login_id trong file user.json
    async def check_login_id(self, user_id, user_manager):
        while True:
            if await user_manager.get_user_credentials(user_id):
                print("Đã có thông tin trong file user.json.")
                return
            else:
                print("Không có thông tin trong file user.json.")
            await asyncio.sleep(10)
    
    # Hàm kiểm tra có thông tin dăng nhập chưa
    async def check_credentials(self, credentials):
        if credentials is None:
            print("Không có thông tin đăng nhập.")
            return "Không có thông tin đăng nhập"  # Không tìm thấy thông tin đăng nhập
        print("Lấy thông tin đăng nhập thành công.")
    
    # Hàm kiểm tra tính hợp lệ của thông tin đăng nhập
    async def check_login_infomation(self, login_id, encrypted_password):
        if not login_id or not encrypted_password:
            print("Thông tin đăng nhập không hợp lệ.")
            return "Thông tin đăng nhập không hợp lệ."
        print("Thông tin đăng nhập hợp lệ")
    
    async def get_notifications(self, user_id, user_manager, auth_manager):
        credentials = await user_manager.get_user_credentials(user_id) # Lấy thông tin đăng nhập từ file
        await self.check_credentials(credentials) # Kiểm tra có thông tin dăng nhập chưa
        login_id, encrypted_password = credentials.get("login_id"), credentials.get("password") # Lấy thông tin đăng nhập
        await self.check_login_infomation(login_id, encrypted_password) # Kiểm tra tính hợp lệ của thông tin đăng nhập
        password = auth_manager.decrypt_password(encrypted_password, user_id) # Tiến hành giải mã mật khẩu
            
            # Tạo task cho các công việc trong hàm này
        async def fetch_data(session):
            try:
                print("Đang truy cập trang đăng nhập...")
                start = time.time()
                login_page = await session.get(self.login_url, timeout=20)
                print(f"Thời gian truy cập: {time.time() - start:.2f} giây")
                
                print("Đang ấy nội dung trang web...")
                page_content = await login_page.text()
                
                print("Đang phân tích nội dung trang web")
                soup = BeautifulSoup(page_content, 'lxml')
                
                print("Đang lấy token xác thực...")
                token = soup.find('input', {'name': '__RequestVerificationToken'})
                
                if not token:
                    message = "Không tìm thấy token xác thực!"
                    print(message)
                    return message

                print("Đang đăng nhập...")
                login_data = {
                    "loginID": login_id, 
                    "password": password, 
                    "__RequestVerificationToken": token['value']
                }
                login_response = await session.post(self.login_url, data=login_data, timeout=20)
                if login_response.status != 200:
                    message = f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"
                    print(message)
                    return message

                print("Đang lấy thông báo...")
                data_response = await session.get(self.data_url, timeout=20)
                if data_response.status != 200:
                    message = f"Không thể lấy dữ liệu từ {self.data_url}. Mã lỗi: {data_response.status}"
                    print(message)
                    return message
                else:
                    print("Lấy dữ liệu thành công.")
                
                soup = BeautifulSoup(await data_response.text(), 'lxml')
                news_list = soup.find('div', id='newsList')
                if not news_list:
                    return "Không tìm thấy danh sách thông báo!"

                notifications = [
                    f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                    for link in news_list.find_all('a', href=True) if '/News/Content' in link['href']
                ][:5]
                
                if notifications:
                    print(f"Đã lấy {len(notifications)} thông báo.")
                return notifications if notifications else "Không có thông báo mới."
            except Exception as e:
                return f"Đã xảy ra lỗi: {e}"

        # Tạo task bất đồng bộ cho việc lấy dữ liệu
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task(fetch_data(session))
            return await task