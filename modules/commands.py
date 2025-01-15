import aiohttp, time
from bs4 import BeautifulSoup
from config import logger

class Commands():
    def __init__(self, husc_notification, user_manager, auth_manager):
        self.login_url = husc_notification.login_url
        self.husc_notification = husc_notification
        self.user_manager = user_manager
        self.auth_manager = auth_manager

    async def handle_login(self, ctx, username: str, password: str):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)
        async with aiohttp.ClientSession() as session:
            login_page = await session.get(self.login_url)
            soup = BeautifulSoup(await login_page.text(), 'html.parser')
            token = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token:
                logger.error("Không tìm thấy token xác thực!")
                await ctx.followup.send("Không tìm thấy token xác thực!")
                return
            login_data = {
                "loginID": username,
                "password": password,
                "__RequestVerificationToken": token['value']
            }
            login_response = await session.post(self.login_url, data=login_data)
            if not await self.husc_notification.is_login_successful(login_response):
                logger.error("Tài khoản mật khẩu không chính xác hoặc đã đăng nhập.")
                await ctx.followup.send("Tài khoản mật khẩu không chính xác hoặc đã đăng nhập.")
                return
            password = self.auth_manager.encrypt_password(password, user_id)
            success = await self.user_manager.save_user_to_file(ctx.user, username, password)
            if success:
                await ctx.followup.send(f"Đăng nhập thành công cho người dùng {ctx.user.name}.")
            else:
                logger.error("Tài khoản đã tồn tại.")
                await ctx.followup.send("Tài khoản đã tồn tại.")
        await self.user_manager.remember_request(user_id, ctx.user.name, "/login")

    async def handle_notifications(self, ctx):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=False)
        
        notifications = None
        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            print("Không có thông tin đăng nhập.")
            notifications = "Không có thông tin đăng nhập."
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
            notifications = await self.husc_notification.read_notifications()

        if notifications == "Không có thông tin đăng nhập.":
            await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
            return
        if notifications == "Không có thông báo mới.":
            await ctx.followup.send(f"**Không có thông báo mới.**")
        else:
            formatted_notifications = "\n".join([f"{notification}" for notification in notifications])
            await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")
        await self.user_manager.remember_request(user_id, ctx.user.name, "/notifications")
    
    async def handle_first(self, ctx):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=False)

        notifications = None
        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            print("Không có thông tin đăng nhập.")
            notifications = "Không có thông tin đăng nhập."
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
            notifications = await self.husc_notification.get_notification_first_line()
        
        if notifications == "Không có thông tin đăng nhập.":
            await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
            return
        if notifications == "Không có thông báo mới.":
            await ctx.followup.send(f"**Không có thông báo mới.**")
        elif notifications:
            await ctx.followup.send(f"**Thông báo mới nhất từ HUSC**:\n{notifications}")
        else:
            await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo.**")
        await self.user_manager.remember_request(user_id, ctx.user.name, "/first")

    async def handle_remind(self, ctx, bot, reminder, reminders, date_time):
        try:
            guild_id = ctx.guild.id if ctx.guild else "DM"
            if guild_id != "DM":
                guild = bot.get_guild(int(guild_id))
                if guild:
                    print(f"Nhắc nhở được tạo trong server: {guild.name} (ID: {guild_id})")
                else:
                    logger.warning(f"Không tìm thấy server với ID: {guild_id}")
            
            await ctx.response.defer()  # Đảm bảo không bị timeout
            await reminders.write_remind_to_file(date_time, reminder, ctx.user.id, ctx.channel.id, guild_id)
            await ctx.followup.send(f"Đặt nhắc nhở '{reminder}' thành công vào lúc: ```{date_time.hour:02d}:{date_time.minute:02d} {date_time.day:02d}-{date_time.month:02d}-{date_time.year}```")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")
