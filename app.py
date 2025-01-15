# Standard
import os, json, time, random, logging, asyncio, html, base64
from datetime import datetime

# Third-party
import discord, aiohttp, pytz, lxml
from discord.ext import tasks, commands
from cryptography.fernet import Fernet
from colorama import init, Fore
from dotenv import load_dotenv
from pytz import timezone
from bs4 import BeautifulSoup

# Local
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands, Reminder
from paths import sent_reminders_path, reminders_path, notifications_path, login_url, data_url
from config import admin_id, logger

# Objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(bot_config.fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url[0], bot_config.fixed_key, notifications_path)
commands = Commands(husc_notification)
reminders = Reminder(reminders_path, sent_reminders_path, bot)

# Initialize 
init(autoreset=True)
timezone = pytz.timezone('Asia/Ho_Chi_Minh')
previous_notifications = None
sent_reminders_set = reminders.load_sent_reminders()

@bot.event
async def on_ready():
    print(f'Bot đăng nhập thành công với tên: {bot.user}')
    await bot.tree.sync()
    print("Đã đồng bộ lệnh")
    send_notifications.start()
    reminder_loop.start()
    update_guilds_info.start()
    print("Ready")

@bot.tree.command(name="login", description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    await commands.handle_login(ctx, username, password, auth_manager, user_manager)

@bot.tree.command(name="notifications", description="Lấy các thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    user_id = ctx.user.id
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
    
    notifications = None
    start_time = time.time()
    credentials = await user_manager.get_user_credentials(user_id)
    if credentials is None:
        print("Không có thông tin đăng nhập.")
        notifications = "Không có thông tin đăng nhập."
    else:
        print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f}s")
        notifications = await husc_notification.read_notifications()

    if notifications == "Không có thông tin đăng nhập.":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
        return
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    else:
        formatted_notifications = "\n".join([f"{notification}" for notification in notifications])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")
    await user_manager.remember_request(user_id, ctx.user.name, "/notifications")

@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    user_id = ctx.user.id
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)

    notifications = None
    start_time = time.time()
    credentials = await user_manager.get_user_credentials(user_id)
    if credentials is None:
        print("Không có thông tin đăng nhập.")
        notifications = "Không có thông tin đăng nhập."
    else:
        print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f} giây")
        notifications = await husc_notification.get_notification_first_line()
    
    if notifications == "Không có thông tin đăng nhập.":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
        return
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    elif notifications:
        await ctx.followup.send(f"**Thông báo mới nhất từ HUSC**:\n{notifications}")
    else:
        await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo.**")
    await user_manager.remember_request(user_id, ctx.user.name, "/first")

@bot.tree.command(name='remind', description="Đặt lịch nhắc nhở")
async def remind(ctx: discord.Interaction, reminder: str, day: int, month: int, year: int, hour: int, minute: int):    
    try:
        guild_id = ctx.guild.id if ctx.guild else "DM"
        if guild_id != "DM":
            guild = bot.get_guild(int(guild_id))
            if guild:
                print(f"Nhắc nhở được tạo trong server: {guild.name} (ID: {guild_id})")
            else:
                logger.warning(f"Không tìm thấy server với ID: {guild_id}")
        
        await ctx.response.defer()  # Đảm bảo không bị timeout
        await reminders.write_remind_to_file(hour, minute, day, month, year, reminder, ctx.user.id, ctx.channel.id, guild_id)
        await ctx.followup.send(f"Đặt nhắc nhở '{reminder}' thành công vào lúc: ```{hour:02d}:{minute:02d} {day:02d}-{month:02d}-{year}```")
    except Exception as e:
        logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")
    
@tasks.loop(seconds=1)
async def reminder_loop():
    await reminders.check_reminders()

@tasks.loop(minutes=1)
async def send_notifications():
    global previous_notifications
    print("\nSTART LOOP")
    
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = []
    if data:
        random_item = random.choice(data)
        random_id = random_item["id"]
        print(f"ID ngẫu nhiên: {random_id}")
    else:
        logging.warning("Danh sách rỗng hoặc không có dữ liệu.")

    user_id = random_id

    if os.path.exists(notifications_path):
        notifications = await husc_notification.read_notifications()
        if notifications:
            previous_notifications = notifications[0].lstrip('- ').strip()
        else:
            previous_notifications = "Empty" 
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
            if previous_notifications != new_notification and previous_notifications is not None or previous_notifications == "Empty":
                formatted_notification = f"- {new_notification}"
                for guild in bot.guilds:
                    text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                    channel = text_channels[0] if text_channels else None
                    if channel:
                        try:
                            await channel.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
                            print(f"Đã gửi thông báo đến kênh: {channel.name} trong server: {guild.name}")
                        except discord.Forbidden:
                            logger.warning(f"Bot không có quyền gửi tin nhắn trong kênh: {channel.name} của server: {guild.name}")
                        except discord.HTTPException as e:
                            logger.error(f"Lỗi HTTP khi gửi tin nhắn đến kênh: {channel.name} của server: {guild.name}, chi tiết: {e}")
                with open("data/notifications.txt", "w", encoding="utf-8") as f:
                    f.writelines([f"- {notification}\n" for notification in notifications])
                previous_notifications = new_notification
            else:
                print("Không có thông báo mới.")
        else:
            print("Không thể lấy thông báo hoặc không có thông báo mới.")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

@tasks.loop(minutes=10)
async def update_guilds_info():
    global guilds_info
    guilds_info = []
    for guild in bot.guilds:
        text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
        channel = text_channels[0] if text_channels else None
        guild_info = {
            'guild_name': guild.name,
            'guild_id': str(guild.id),
            'channel_name': channel.name,
            'channel_id': str(channel.id),
            'member_count': guild.member_count
        }
        guilds_info.append(guild_info)
    with open("data/guilds_info.json", "w", encoding="utf-8") as f:
        json.dump(guilds_info, f, ensure_ascii=False, indent=4)

bot.run(bot_config.token)
