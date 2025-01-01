import aiohttp
from bs4 import BeautifulSoup

class Commands():
    def __init__(self, husc_notification):
        self.login_url = husc_notification.login_url
        self.husc_notification = husc_notification

    async def handle_login(self, ctx, username: str, password: str, auth_manager, user_manager):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)
        async with aiohttp.ClientSession() as session:
            login_page = await session.get(self.login_url)
            soup = BeautifulSoup(await login_page.text(), 'html.parser')
            token = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token:
                await ctx.followup.send("Không tìm thấy token xác thực!")
                return
            login_data = {
                "loginID": username,
                "password": password,
                "__RequestVerificationToken": token['value']
            }
            login_response = await session.post(self.login_url, data=login_data)
            if not await self.husc_notification.is_login_successful(login_response):
                await ctx.followup.send("Tài khoản mật khẩu không chính xác hoặc đã đăng nhập.")
                return
            password = auth_manager.encrypt_password(password, user_id)
            success = await user_manager.save_user_to_file(ctx.user, username, password)
            if success:
                await ctx.followup.send(f"Đăng nhập thành công cho người dùng {ctx.user.name}.")
            else:
                await ctx.followup.send("Tài khoản đã tồn tại.")
        await user_manager.remember_request(user_id, ctx.user.name, "/login")
