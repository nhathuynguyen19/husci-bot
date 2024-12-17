import discord, aiohttp, os, json, html, asyncio, base64, pytz, lxml
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from config import fixed_key, id_admin
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone

# trang web
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"

# Tạo một danh sách để lưu những nhắc nhở đã được gửi
sent_reminders_file = "sent_reminders.txt"

# Chọn múi giờ, ví dụ GMT+7 (UTC+7)
timezone = pytz.timezone('Asia/Ho_Chi_Minh')

# Biến toàn cục lưu đường dẫn file
remind_file = 'remind.txt'

# Đọc các nhắc nhở đã gửi từ tệp
def load_sent_reminders():
    try:
        # Kiểm tra nếu file đã tồn tại và đọc
        with open(sent_reminders_file, 'r', encoding='utf-8') as f:
            reminders = {line.strip() for line in f}  # Dùng set để loại bỏ nhắc nhở trùng lặp
        return reminders
    except FileNotFoundError:
        # Nếu file không tồn tại, trả về set rỗng
        return set()
    except Exception as e:
        print(f"Lỗi khi đọc tệp {sent_reminders_file}: {e}")
        return set()

# Ghi các nhắc nhở đã gửi vào tệp
def save_sent_reminders(sent_reminders):
    try:
        # Mở file để ghi
        with open(sent_reminders_file, 'w', encoding='utf-8') as f:
            # Ghi từng nhắc nhở vào file
            for reminder in sent_reminders:
                f.write(f"{reminder}\n")  # Ghi mỗi nhắc nhở vào một dòng
        print(f"Nhắc nhở đã được lưu vào tệp {sent_reminders_file}")
    except Exception as e:
        print(f"Lỗi khi ghi vào tệp {sent_reminders_file}: {e}")

def add_sent_reminder(reminder):
    sent_reminders = load_sent_reminders()  # Đọc các nhắc nhở đã gửi

    # Nếu sent_reminders không phải là set, chuyển nó thành set
    if not isinstance(sent_reminders, set):
        sent_reminders = set(sent_reminders)

    if reminder not in sent_reminders:
        sent_reminders.add(reminder)  # Thêm nhắc nhở mới vào set
        save_sent_reminders(sent_reminders)  # Lưu lại vào file

# Hàm ghi lệnh nhắc nhở vào file
def write_remind_to_file(hour, minute, day, month, year, reminder, user_id, guild_id, channel_id):
    """
    Ghi lệnh nhắc nhở vào file remind.txt.
    """
    try:
        with open(remind_file, 'a') as file:
            reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        print(f"Lỗi khi ghi nhắc nhở vào file: {e}")

# Hàm đọc lệnh nhắc nhở từ file
def read_remind_from_file():
    try:
        with open(remind_file, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        return []  # Trả về danh sách rỗng nếu file không tồn tại
        
# Hàm kiểm tra và gửi nhắc nhở
async def check_reminders():
    now = datetime.now(timezone)
    # print(f"check reminder at {now}")
    if now.tzinfo is None:  # Nếu `now` chưa có thông tin múi giờ
        now = timezone.localize(now)  # Áp dụng múi giờ nếu cần
        
    reminders = read_remind_from_file()  # Đọc tất cả các nhắc nhở từ file
    
    sent_reminders = load_sent_reminders()  # Đọc các nhắc nhở đã gửi

    for reminder in reminders:
        try:
            # Tách thông tin nhắc nhở từ dòng
            reminder_parts = reminder.strip().split(' - ', 4)
            if len(reminder_parts) < 5:
                print(f"Lỗi: Nhắc nhở không hợp lệ: {reminder}")
                continue  # Bỏ qua dòng không hợp lệ

            reminder_time_str = reminder_parts[0]
            reminder_msg = reminder_parts[1]
            user_id = int(reminder_parts[2])
            channel_id = int(reminder_parts[4])

            # Chuyển đổi thời gian nhắc nhở
            reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%d %H:%M')
            reminder_time = timezone.localize(reminder_time)
            
            time_diff = 0
            time_diff = abs((reminder_time - now).total_seconds())  # Chênh lệch tính bằng giây
            if time_diff < 1:  # Nếu thời gian nhắc nhở đã đến
                # Kiểm tra xem nhắc nhở này đã được gửi chưa
                reminder_key = f"{reminder_time} - {reminder_msg} - {user_id} - {channel_id}"
                if reminder_key in sent_reminders:
                    print(f"Nhắc nhở đã được gửi trước đó.")
                    continue  # Bỏ qua nhắc nhở đã gửi
                
                # Lấy kênh từ ID
                channel = bot.get_channel(channel_id)
                if channel:
                    # Gửi nhắc nhở vào kênh
                    await channel.send(f"<@{user_id}> Nhắc nhở: {reminder_msg}")
                    print(f"Nhắc nhở gửi đến kênh {channel_id}: {reminder_msg}")
                else:
                    print(f"Không tìm thấy kênh với ID: {channel_id}")
                
                # Gửi nhắc nhở qua DM cho người dùng
                user = await bot.fetch_user(user_id)  # Dùng fetch_user thay vì get_user
                if user:
                    await user.send(f"Nhắc nhở: {reminder_msg}")
                    print(f"Nhắc nhở gửi đến người dùng {user_id}: {reminder_msg}")
                
                # Đánh dấu nhắc nhở đã gửi
                add_sent_reminder(reminder_key)  # Thêm nhắc nhở mới vào file
            
        except Exception as e:
            print(f"Lỗi khi xử lý nhắc nhở: {e}")

# Hàm ghi lệnh vào file
def write_remind_to_file(hour, minute, day, month, year, reminder, user_id, guild_id, channel_id):
    """
    Ghi lệnh nhắc nhở vào file remind.txt.
    """
    try:
        with open(remind_file, 'a', encoding='utf-8') as file:
            reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        print(f"Lỗi khi ghi nhắc nhở vào file: {e}")

# Biến lưu trữ thông báo trước đó
previous_notifications = []
        
# objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url, fixed_key)

# đọc nhắc nhở từ file sent_reminder.txt
sent_reminders = load_sent_reminders()  # Đọc từ tệp khi chương trình khởi động

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

# Lệnh hẹn giờ với ngày giờ cụ thể
@bot.tree.command(name='remind_all', description="Đặt lịch nhắc nhở")
async def remind_all(interaction: discord.Interaction, hour: int, minute: int, day: int, month: int, year: int, *, reminder: str):
    
    guild_id = interaction.guild.id if interaction.guild else "DM"
    if guild_id != "DM":
        guild = bot.get_guild(int(guild_id))
        if guild:
            print(f"Nhắc nhở được tạo trong server: {guild.name} (ID: {guild_id})")
        else:
            print(f"Không tìm thấy server với ID: {guild_id}")

    write_remind_to_file(hour, minute, day, month, year, reminder, interaction.user.id, guild_id, interaction.channel.id)

    # Lấy thời gian hiện tại
    now = datetime.now(timezone)

    # Tạo datetime của thời điểm hẹn giờ
    target_time = datetime(year, month, day, hour, minute)
    target_time = timezone.localize(target_time)  # Thêm múi giờ vào target_time

    # Nếu thời gian hẹn giờ đã qua, thông báo người dùng và hẹn lại vào năm sau
    if target_time < now:
        target_time = target_time.replace(year=now.year + 1)
        
    # Hoãn phản hồi để không gặp lỗi
    await interaction.response.defer()
    
    # Thông báo người dùng
    mesage = f"Đặt lời nhắc thành công vào {target_time.strftime('%d/%m/%Y %H:%M')}."
    print(mesage)
    await interaction.followup.send(mesage)
    
# Hàm chạy lặp lại mỗi 1 phút để kiểm tra nhắc nhở
async def reminder_loop():
    while True:
        await check_reminders()
        await asyncio.sleep(1) 

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


bot.run(bot_config.token)
asyncio.run(reminder_loop())
