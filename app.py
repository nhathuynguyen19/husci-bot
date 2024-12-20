import discord, aiohttp, os, json, html, asyncio, base64, pytz, lxml
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from config import fixed_key, id_admin
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone

def load_sent_reminders():
    try:
        with open(sent_reminders_file, 'r', encoding='utf-8') as f:
            reminders = {line.strip() for line in f}
        return reminders
    except FileNotFoundError:
        print(f"Tệp {sent_reminders_file} không tồn tại. Trả về tập hợp rỗng.")
        return set()
    except Exception as e:
        print(f"Lỗi khi đọc tệp {sent_reminders_file}: {e}")
        return set()

def save_sent_reminders(sent_reminders):
    try:
        with open(sent_reminders_file, 'w', encoding='utf-8') as f:
            for reminder in sent_reminders:
                f.write(f"{reminder}\n")
        print(f"Nhắc nhở đã được lưu vào tệp {sent_reminders_file}")
    except Exception as e:
        print(f"Lỗi khi ghi vào tệp {sent_reminders_file}: {e}")

def add_sent_reminder(reminder):
    sent_reminders = load_sent_reminders()
    if not isinstance(sent_reminders, set):
        sent_reminders = set(sent_reminders)
    if reminder not in sent_reminders:
        sent_reminders.add(reminder) 
        save_sent_reminders(sent_reminders)

def write_remind_to_file(hour, minute, day, month, year, reminder, user_id, guild_id, channel_id):
    try:
        with open(remind_file, 'a') as file:
            reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        print(f"Lỗi khi ghi nhắc nhở vào file: {e}")

def read_remind_from_file():
    try:
        with open(remind_file, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        return []
        
async def check_reminders():
    now = datetime.now(timezone)
    if now.tzinfo is None: 
        now = timezone.localize(now) 
    reminders = read_remind_from_file() 
    sent_reminders = load_sent_reminders()
    for reminder in reminders:
        try:
            reminder_parts = reminder.strip().split(' - ', 4)
            if len(reminder_parts) < 5:
                print(f"Lỗi: Nhắc nhở không hợp lệ: {reminder}")
                continue
            reminder_time_str = reminder_parts[0]
            reminder_msg = reminder_parts[1]
            user_id = int(reminder_parts[2])
            channel_id = int(reminder_parts[4])
            reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%d %H:%M')
            reminder_time = timezone.localize(reminder_time)
            time_diff = 0
            time_diff = abs((reminder_time - now).total_seconds())
            if time_diff < 1: 
                reminder_key = f"{reminder_time} - {reminder_msg} - {user_id} - {channel_id}"
                if reminder_key in sent_reminders:
                    print(f"Nhắc nhở đã được gửi trước đó.")
                    continue 
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(f"<@{user_id}> Nhắc nhở: {reminder_msg}")
                    print(f"Nhắc nhở gửi đến kênh {channel_id}: {reminder_msg}")
                else:
                    print(f"Không tìm thấy kênh với ID: {channel_id}")
                user = await bot.fetch_user(user_id)  
                if user:
                    await user.send(f"Nhắc nhở: {reminder_msg}")
                    print(f"Nhắc nhở gửi đến người dùng {user_id}: {reminder_msg}")
                add_sent_reminder(reminder_key) 
        except Exception as e:
            print(f"Lỗi khi xử lý nhắc nhở: {e}")

def write_remind_to_file(hour, minute, day, month, year, reminder, user_id, guild_id, channel_id):
    try:
        with open(remind_file, 'a', encoding='utf-8') as file:
            reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        print(f"Lỗi khi ghi nhắc nhở vào file: {e}")
        
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"
sent_reminders_file = "sent_reminders.txt"
timezone = pytz.timezone('Asia/Ho_Chi_Minh')
remind_file = 'remind.txt'
previous_notifications = None
sent_reminders = load_sent_reminders()

# objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url, fixed_key)
commands = Commands(husc_notification)

@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    print("Đang đồng bộ lệnh...")
    await bot.tree.sync()
    print("Đồng bộ lệnh thành công.")
    print("Đang tự động lấy thông báo định kỳ...")
    send_notifications.start()
    reminder_loop.start()
    print("Bot đã sẵn sàng nhận lệnh!")

@bot.tree.command(name="login", description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    await commands.handle_login(ctx, username, password, auth_manager, user_manager)

@bot.tree.command(name="notifications", description="Lấy các thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    user_id = ctx.user.id
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
    task = asyncio.create_task(husc_notification.get_notifications(user_id, user_manager, auth_manager))
    notifications = await task 
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

@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    user_id = ctx.user.id
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
    task = asyncio.create_task(husc_notification.get_notifications(user_id, user_manager, auth_manager))
    notifications = await task
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

@bot.tree.command(name='remindall', description="Đặt lịch nhắc nhở")
async def remindall(interaction: discord.Interaction, reminder: str, day: int, month: int, year: int, hour: int, minute: int):    
    guild_id = interaction.guild.id if interaction.guild else "DM"
    if guild_id != "DM":
        guild = bot.get_guild(int(guild_id))
        if guild:
            print(f"Nhắc nhở được tạo trong server: {guild.name} (ID: {guild_id})")
        else:
            print(f"Không tìm thấy server với ID: {guild_id}")
    write_remind_to_file(hour, minute, day, month, year, reminder, interaction.user.id, guild_id, interaction.channel.id)
    now = datetime.now(timezone)
    target_time = datetime(year, month, day, hour, minute)
    target_time = timezone.localize(target_time)
    if target_time < now:
        target_time = target_time.replace(year=now.year + 1)
    await interaction.response.defer()
    mesage = f"Đặt lời nhắc thành công vào {target_time.strftime('%d/%m/%Y %H:%M')}."
    print(mesage)
    await interaction.followup.send(mesage)
    
@tasks.loop(seconds=1)
async def reminder_loop():
    await check_reminders()

@tasks.loop(minutes=1)
async def send_notifications():
    global previous_notifications
    print("=== Start loop get notifications ===")
    user_id = id_admin
    if os.path.exists("notifications.txt"):
        with open("notifications.txt", "r", encoding="utf-8") as f:
            previous_notifications = f.read().strip() 
            previous_notifications = previous_notifications.lstrip('- ').strip()
    else:
        previous_notifications = None 
    print("Đang tiến hành kiểm tra đăng nhập...")
    await husc_notification.check_login_id(user_id, user_manager)
    try:
        print("Đang lấy thông báo...")
        task = asyncio.create_task(husc_notification.get_notifications(user_id, user_manager, auth_manager))
        notifications = await task 
        if isinstance(notifications, list) and notifications:
            new_notification = notifications[0] 
            if previous_notifications != new_notification and previous_notifications is not None:  
                formatted_notification = f"- {new_notification}"
                for guild in bot.guilds:
                    text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                    channel = text_channels[0] if text_channels else None
                    if channel:
                        try:
                            await channel.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
                            print(f"Đã gửi thông báo đến kênh: {channel.name} trong server: {guild.name}")
                        except discord.Forbidden:
                            print(f"Bot không có quyền gửi tin nhắn trong kênh: {channel.name} của server: {guild.name}")
                        except discord.HTTPException as e:
                            print(f"Lỗi HTTP khi gửi tin nhắn đến kênh: {channel.name} của server: {guild.name}, chi tiết: {e}")
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