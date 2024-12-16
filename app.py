import discord, aiohttp, os, json, datetime, html, asyncio, base64
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from config import fixed_key, id_admin
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# trang web
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"

# Biến lưu trữ thông báo trước đó
previous_notifications = []
        
# objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url, fixed_key)

# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    print("Đang đồng bộ lệnh...")
    await bot.tree.sync()  # Đồng bộ lệnh app_commands sau khi bot đã sẵn sàng
    print("Đồng bộ lệnh thành công.")
    print("Đang tự động lấy thông báo định kỳ...")
    send_notifications.start() # Bắt đầu vòng lặp gửi thông báo tự động
    print("Bot đã sẵn sàng nhận lệnh!")

# Lệnh đăng nhập
@bot.tree.command(name="login", description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=True)
    
    async with aiohttp.ClientSession() as session:
        # Truy cập trang đăng nhập
        login_page = await session.get(login_url)
        soup = BeautifulSoup(await login_page.text(), 'html.parser')
        
        # Lấy token xác thực từ trang
        token = soup.find('input', {'name': '__RequestVerificationToken'})
        if not token:
            await ctx.followup.send("Không tìm thấy token xác thực!")
            return
        
        login_data = {
            "loginID": username,
            "password": password,
            "__RequestVerificationToken": token['value']
        }
        
        # Gửi yêu cầu đăng nhập
        login_response = await session.post(login_url, data=login_data)
        
        if not await husc_notification.is_login_successful(login_response):
            await ctx.followup.send("Tài khoản mật khẩu không chính xác hoặc đã đăng nhập.")
            return
        
        # mã hóa mật khẩu để lưu
        password = auth_manager.encrypt_password(password, user_id, fixed_key)
        
         # Lưu thông tin người dùng vào file
        success = await user_manager.save_user_to_file(ctx.user, username, password)
        if success:
            await ctx.followup.send(f"Đăng nhập thành công cho người dùng {ctx.user.name}.")
        else:
            await ctx.followup.send("Tài khoản đã tồn tại.")
        
    await user_manager.remember_request(user_id, ctx.user.name, "/login")


# Lệnh lấy 5 thông báo đầu
@bot.tree.command(name="notifications", description="Lấy các thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
            
    notifications = await husc_notification.get_notifications(user_id, user_manager, auth_manager)  # Gọi hàm lấy thông báo
    
    if notifications == "Không có thông tin đăng nhập":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
        return
    
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    else:
        top_notifications = notifications[:5]
        formatted_notifications = "\n".join([f"- {notification}" for notification in top_notifications])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")
    
    await user_manager.remember_request(user_id, ctx.user.name, "/notifications")


# Lệnh lấy thông báo mới nhất
@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
                
    notifications = await husc_notification.get_notifications(user_id, user_manager, auth_manager)  # Gọi hàm lấy thông báo
    
    if notifications == "Không có thông tin đăng nhập":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
        return


    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    elif isinstance(notifications, list) and notifications:
        first_notification = notifications[0]
        formatted_notification = f"- {first_notification}"
        await ctx.followup.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
    else:
        await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo.**")
        
    await user_manager.remember_request(user_id, ctx.user.name, "/first")


# lệnh tự động thông báo mỗi khi có thông báo mới
@tasks.loop(minutes=5)
async def send_notifications():
    global previous_notifications

    user_id = id_admin
    
    print("Đang tiến hành kiểm tra đăng nhập...")
    # Chờ cho đến khi có login_id trong user.json
    await husc_notification.check_login_id(user_id, user_manager)
    
    try:
        notifications = await husc_notification.get_notifications(user_id, user_manager, auth_manager)  # Gọi hàm lấy thông báo
        
        if isinstance(notifications, list) and notifications:
            new_notification = notifications[0]  # Lấy thông báo đầu tiên mới

            if previous_notifications != new_notification:  # So sánh thông báo mới với thông báo trước đó
                if previous_notifications: # nếu là lần đầu
                    formatted_notification = f"- {new_notification}"

                    guild = bot.guilds[0] if bot.guilds else None
                    channel = guild.text_channels[0] if guild and guild.text_channels else None

                    if channel:
                        await channel.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")

                    with open("notifications.txt", "w", encoding="utf-8") as f:
                        f.write(formatted_notification)

                    previous_notifications = new_notification
                else: # nếu là lần > 1
                    formatted_notification = f"- {new_notification}"

                    with open("notifications.txt", "w", encoding="utf-8") as f:
                        f.write(formatted_notification)

                    previous_notifications = new_notification
            else:
                print("Không có thông báo mới.")
        else:
            print("Không thể lấy thông báo hoặc không có thông báo mới.")
    except Exception as e:
        print(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

# Chạy bot với token
bot.run(bot_config.token)
