
import time, aiohttp, asyncio
from config import logger
from bs4 import BeautifulSoup
from paths import login_url, data_url, temp_path
from modules.utils.file import save_txt, load_json, save_json

class UsersHandler:
    def __init__(self, auth_manager, bot, users_path):
        self.auth_manager = auth_manager
        self.bot = bot
        self.users_path = users_path

    async def process_result(self, result):
        users_data = await load_json(self.users_path)

        # Cập nhật sms cho user có id trùng với id trong result
        for user in users_data:
            if user["id"] == result["id"]:
                user["sms"] = result["sms"]  # Chỉ cập nhật sms
                break

        await save_json(self.users_path, users_data)

    async def fetch_data(self, session, login_id, password, user):
        try:
            page = await session.get(login_url)
            html = BeautifulSoup(await page.text(), 'html.parser')
            token = html.find('input', {'name': '__RequestVerificationToken'})['value']
            login_data = {
                "loginID": login_id,
                "password": password,
                "__RequestVerificationToken": token
            }
            await session.post(login_url, data=login_data)

            while True:
                read_page = await session.post(data_url[1], data=login_data)
                html = BeautifulSoup(await read_page.text(), 'html.parser')
                emails_list = html.find('form', id='__formMessageList')
                
                if not emails_list:
                    logger.warning("Không tìm thấy danh sách tin nhắn!")
                    await asyncio.sleep(10)
                    continue

                emails = [
                    f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                    for link in emails_list.find_all('a', href=True) if '/Message/Details' in link['href']
                ][:5]

                Changed = False
                if emails:
                    latest_email = emails[0]
                    
                    if "sms" not in user:
                        user["sms"] = latest_email
                        Changed = True
                    else:
                        if user["sms"] != latest_email:
                            Changed = True
                            old_message = user["sms"]
                            user["sms"] = latest_email
                            user_id = user['id']
                            user_obj = await self.bot.fetch_user(int(user_id))
                            if user_obj and old_message != "":
                                await user_obj.send(f"**Tin nhắn mới**:\n{latest_email}")
                                print(f"Tin nhắn mới đã gửi đến {user_id}: {latest_email}")
                            else:
                                print(f"Không tìm thấy người dùng với ID: {user_id}")
                                
                    if Changed:
                        result = {
                            "id": user["id"],
                            "sms": user.get("sms", "")
                        }
                        await self.process_result(result)

                await asyncio.sleep(5)

        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")

    async def _handle_user_data(self, login_id, password, user):
        async with aiohttp.ClientSession() as session:
            print(f"Session cho {login_id} đã được tạo và sử dụng.")
            await self.fetch_data(session, login_id, password, user)

    async def handle_users(self):
        users_data = await load_json(self.users_path)

        tasks = []
        for user in users_data:
            login_id, encrypted_password = user.get("login_id"), user.get("password")
            start_time = time.time()
            password = await self.auth_manager.decrypt_password(encrypted_password, user.get("id"), start_time)

            task = asyncio.create_task(self._handle_user_data(login_id, password, user))
            tasks.append(task)

