import aiohttp, time, os, discord
from bs4 import BeautifulSoup
from config import logger, load_md_line_by_line
from modules.utils.http import is_login_successful
from modules.utils.file import add_reminder, load_json, save_json, load_md
from paths import data_url, users_path, BASE_DIR, unique_member_ids_path, path_creator
from modules.utils.autopush import push_to_git

class Commands():
    def __init__(self, husc_notification, user_manager, auth_manager, loops, emails_handler):
        self.login_url = husc_notification.login_url
        self.husc_notification = husc_notification
        self.user_manager = user_manager
        self.auth_manager = auth_manager
        self.loops = loops
        self.emails_handler = emails_handler

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
                await ctx.followup.send("**Không tìm thấy token xác thực!**")
                return
            login_data = {
                "loginID": username,
                "password": password,
                "__RequestVerificationToken": token['value']
            }
            login_response = await session.post(self.login_url, data=login_data)
            if not await is_login_successful(login_response):
                logger.error("Tài khoản mật khẩu không chính xác hoặc đã đăng nhập")
                await ctx.followup.send("**Ủa bạn ơi, tài khoản mật khẩu không chính xác hoặc đã đăng nhập rồi!**")
                return
            password = await self.auth_manager.encrypt_password(password, user_id)
            success = await self.user_manager.save_user_to_file_when_login(ctx.user, username, password)
            if success:
                data = await load_json(users_path)
                length = len(data)
                data_members = await load_json(unique_member_ids_path)
                await ctx.followup.send(f"**Chào mừng {ctx.user.name} gia nhập quân đoàn Husciers cùng với {length - 1}/{data_members['total_unique_members']} thành viên khác**")
            else:
                logger.error("Tài khoản đã tồn tại")
                await ctx.followup.send(f"**Ủa bạn, bạn đã đăng nhập rồi mà! {ctx.user.name} phải không?**")
        await self.user_manager.remember_request(user_id, ctx.user.name, "/login")

    async def handle_logout(self, ctx):
        condition = False
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=False)
        users = await load_json(users_path)
        length = len(users)

        for user in users:
            if user_id == user.get("id"):
                users.remove(user)
                condition = True
                logger.warning(f"**Người dùng {user.get("name")} đã đăng xuất khỏi server Huscier**")
                await ctx.followup.send(f"**Người dùng {user.get("name")} đã đăng xuất khỏi server Husci**")
                break

        if not condition:
            await ctx.followup.send("**Vui lòng đăng nhập tài khoản Student**")
        if condition:
            await save_json(users_path, users)
        await self.user_manager.remember_request(user_id, ctx.user.name, "/logout")

    async def handle_notifications(self, ctx):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=False)
        
        notifications = None
        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            notifications = "Không có thông tin đăng nhập"
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
            notifications = await self.husc_notification.read_notifications()

        if notifications == "Không có thông tin đăng nhập":
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        if notifications == "Không có thông báo mới":
            await ctx.followup.send(f"**Không có thông báo mới**")
        else:
            formatted_notifications = "\n".join([f"{notification}" for notification in notifications])
            await ctx.followup.send(f"**Các thông báo mới từ Husci:**\n{formatted_notifications}")
        await self.user_manager.remember_request(user_id, ctx.user.name, "/notifications")
    
    async def handle_first(self, ctx):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=False)

        notifications = None
        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            notifications = "Không có thông tin đăng nhập"
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
            notifications = await self.husc_notification.get_notification_first_line()
        
        if notifications == "Không có thông tin đăng nhập":
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        if notifications == "Không có thông báo mới":
            await ctx.followup.send(f"**Không có thông báo mới**")
        elif notifications:
            await ctx.followup.send(f"**Thông báo mới nhất từ Husci**:\n{notifications}")
        else:
            await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo**")
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
            await add_reminder(date_time, reminder, ctx.user.id, ctx.channel.id, guild_id)
            await ctx.followup.send(f"**Đặt nhắc nhở** `{reminder}` **thành công vào lúc:**```{date_time.hour:02d}:{date_time.minute:02d} {date_time.day:02d}-{date_time.month:02d}-{date_time.year}```")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")
        await self.user_manager.remember_request(ctx.user.id, ctx.user.name, "/remind")

    async def handle_message(self, ctx):
        user_id = ctx.user.id
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)
            
        await self.user_manager.remember_request(user_id, ctx.user.name, "/message")

        email = None
        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            email = "Không có thông tin đăng nhập"
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
            email = credentials["sms"]
        
        if email == "Không có thông tin đăng nhập":
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        if email == "Không có tin nhắn mới":
            await ctx.followup.send(f"**Không có tin nhắn mới**")
        elif email:
            await ctx.followup.send(f"**Tin nhắn mới nhất**:\n{email}")
        else:
            await ctx.followup.send(f"**Chưa có tin nhắn**")

    async def handle_last_score(self, ctx, bot):
        user_id = ctx.user.id
        users = await load_json(users_path)
        login_id = None

        await self.user_manager.remember_request(user_id, ctx.user.name, "/lastscore")

        for user in users:
            if user["id"] == user_id:
                login_id = user["login_id"]
        
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)

        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")

        user_obj = await bot.fetch_user(int(user_id))
        output_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', 'last', f"{login_id}.md")
        path_creator(output_path)
        
        if user_obj:
            if os.path.exists(output_path):
                message = "**Cập nhật cuối**:\n```"
                message += await load_md(output_path)
                message += "\n```"
                await ctx.followup.send(message)
            else:
                await ctx.followup.send(f"**Không có cập nhật cuối**")
        else:
            await ctx.followup.send(f"**Error! Không tìm thấy người dùng với ID: {user_obj}**")
            logger.warning(f"Không tìm thấy người dùng với ID: {user_obj}")

    async def handle_full_score(self, ctx, bot):
        user_id = ctx.user.id
        users = await load_json(users_path)
        login_id = None
        
        await self.user_manager.remember_request(user_id, ctx.user.name, "/scoretable")

        for user in users:
            if user["id"] == user_id:
                login_id = user["login_id"]
        
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)

        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")

        user_obj = await bot.fetch_user(int(user_id))
        if user_obj:
            output_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', 'full', f"{login_id}_full.md")
            path_creator(output_path)
            
            output = await load_md(output_path)
            await ctx.followup.send(f"**Lịch sử quá trình học tập:**\n```\n{output}\n```")
        else:
            await ctx.followup.send(f"**Error! Không tìm thấy người dùng với ID: {user_obj}**")
            logger.warning(f"Không tìm thấy người dùng với ID: {user_obj}")

    async def handle_time_table_week(self, ctx, bot):
        user_id = ctx.user.id
        users = await load_json(users_path)
        login_id = None
        await self.user_manager.remember_request(user_id, ctx.user.name, "/timetable")

        for user in users:
            if user["id"] == user_id:
                login_id = user["login_id"]
        
        if not ctx.response.is_done():
            await ctx.response.defer(ephemeral=True)

        start_time = time.time()
        credentials = await self.user_manager.get_user_credentials(user_id)
        if credentials is None:
            logger.warning("Không có thông tin đăng nhập")
            await ctx.followup.send("**Chưa đăng nhập tài khoản Student! Dùng lệnh `/login` để đăng nhập**")
            return
        else:
            print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")

        user_obj = await bot.fetch_user(int(user_id))
        if user_obj:
            week_md_path = os.path.join(BASE_DIR, 'data', 'schedule', 'markdown', 'week', f"{login_id}.md")            
            path_creator(week_md_path)
            
            output = await load_md(week_md_path)
            await ctx.followup.send(f"**Thời khóa biểu tuần:**\n```\n{output}\n```")
        else:
            await ctx.followup.send(f"**Error! Không tìm thấy người dùng với ID: {user_obj}**")
            logger.warning(f"Không tìm thấy người dùng với ID: {user_obj}")