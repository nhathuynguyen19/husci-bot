import asyncio, aiohttp, html
from bs4 import BeautifulSoup

class HUSCNotifications:
    def __init__(self, login_url, data_url, fixed_key):
        self.login_url = login_url
        self.data_url = data_url
        self.key = fixed_key

    async def is_login_successful(self, response):
        content = await response.text()
        decoded_content = html.unescape(content)
        soup = BeautifulSoup(decoded_content, 'html.parser')
        error = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')
        if error:
            print("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
            return False
        print("Đăng nhập thành công!")
        return True
    
    # Hàm kiểm tra thông tin login_id trong file user.json
    async def check_login_id(self, user_id, user_manager):
        print("__________")
        while True:
            if await user_manager.get_user_credentials(user_id):
                print("Đã có thông tin trong file user.json.")
                return
            else:
                print("Không có thông tin trong file user.json.")
            
            # Nếu chưa có login_id, đợi và kiểm tra lại sau 10 giây
            await asyncio.sleep(10)
            
    async def get_notifications(self, user_id, user_manager, auth_manager):
        print("__________")
        # Lấy thông tin đăng nhập từ file
        credentials = await user_manager.get_user_credentials(user_id)
        
        # kiểm tra có thông tin dăng nhập chưa
        if credentials is None:
            print("Không có thông tin đăng nhập.")
            return "Không có thông tin đăng nhập"  # Không tìm thấy thông tin đăng nhập
        print("Lấy thông tin đăng nhập thành công.")

        # Lấy thông tin đăng nhập
        login_id, encrypted_password = credentials.get("login_id"), credentials.get("password")
        if not login_id or not encrypted_password:
            print("Thông tin đăng nhập không hợp lệ.")
            return "Thông tin đăng nhập không hợp lệ."
        print("Thông tin đăng nhập hợp lệ")
        
        # giải mã mật khẩu
        print("Đang tiến hành giải mã...")
        password = auth_manager.decrypt_password(encrypted_password, user_id)
        print("Giải mã thành công.")
            
        try:
            async with aiohttp.ClientSession() as session:
                print("Đang truy cập trang đăng nhập...")
                login_page = await session.get(self.login_url)
                soup = BeautifulSoup(await login_page.text(), 'html.parser')
                
                token = soup.find('input', {'name': '__RequestVerificationToken'})
                if not token:
                    return "Không tìm thấy token xác thực!"

                print("Đang đăng nhập...")
                login_data = {
                    "loginID": login_id, 
                    "password": password, 
                    "__RequestVerificationToken": token['value']
                }
                login_response = await session.post(self.login_url, data=login_data)
                if login_response.status != 200:
                    return f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"

                print("Đang lấy thông báo...")
                data_response = await session.get(self.data_url)
                if data_response.status != 200:
                    return f"Không thể lấy dữ liệu từ {self.data_url}. Mã lỗi: {data_response.status}"
                else:
                    print("Lấy thông báo thành công.")
                
                soup = BeautifulSoup(await data_response.text(), 'html.parser')
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