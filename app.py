import discord, aiohttp, os, json, html, asyncio, base64, pytz, lxml, time, random
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from config import admin_id
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sent_reminders():
    try:
        with open(sent_reminders_file, 'r', encoding='utf-8') as f:
            reminders = {line.strip() for line in f}
        return reminders
    except FileNotFoundError:
        logger.warning(f"Tệp {sent_reminders_file} không tồn tại. Trả về tập hợp rỗng.")
        return set()
    except Exception as e:
        logger.error(f"Lỗi khi đọc tệp {sent_reminders_file}: {e}")
        return set()

def save_sent_reminders(sent_reminders):
    try:
        with open(sent_reminders_file, 'w', encoding='utf-8') as f:
            for reminder in sent_reminders:
                f.write(f"{reminder}\n")
        logger.info(f"Nhắc nhở đã được lưu vào tệp {sent_reminders_file}")
    except Exception as e:
        logger.error(f"Lỗi khi ghi vào tệp {sent_reminders_file}: {e}")

def add_sent_reminder(reminder):
    sent_reminders = load_sent_reminders()
    if not isinstance(sent_reminders, set):
        sent_reminders = set(sent_reminders)
    if reminder not in sent_reminders:
        sent_reminders.add(reminder) 
        save_sent_reminders(sent_reminders)

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
                logger.error(f"Lỗi: Nhắc nhở không hợp lệ: {reminder}")
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
                    logger.info(f"Nhắc nhở đã được gửi trước đó.")
                    continue 
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(f"<@{user_id}> Nhắc nhở: {reminder_msg}")
                    logger.info(f"Nhắc nhở gửi đến kênh {channel_id}: {reminder_msg}")
                else:
                    logger.warning(f"Không tìm thấy kênh với ID: {channel_id}")
                user = await bot.fetch_user(user_id)  
                if user:
                    await user.send(f"Nhắc nhở: {reminder_msg}")
                    logger.info(f"Nhắc nhở gửi đến người dùng {user_id}: {reminder_msg}")
                add_sent_reminder(reminder_key) 
        except Exception as e:
            logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")

def write_remind_to_file(hour, minute, day, month, year, reminder, user_id, guild_id, channel_id):
    try:
        with open(remind_file, 'a', encoding='utf-8') as file:
            reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            logger.info(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        logger.error(f"Lỗi khi ghi nhắc nhở vào file: {e}")

def get_notification_first_line():
    with open('notifications.txt', 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()  # Chỉ lấy dòng đầu tiên và loại bỏ ký tự dư thừa
    return first_line

login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"
sent_reminders_file = "sent_reminders.txt"
timezone = pytz.timezone('Asia/Ho_Chi_Minh')
remind_file = 'remind.txt'
previous_notifications = None
sent_reminders = load_sent_reminders()
guilds_info = []

# objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(bot_config.fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url, bot_config.fixed_key)
commands = Commands(husc_notification)

@bot.event
async def on_ready():
    logger.info(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    logger.info("Đang đồng bộ lệnh...")
    await bot.tree.sync()
    logger.info("Đồng bộ lệnh thành công.")
    logger.info("Đang tự động lấy thông báo định kỳ...")
    send_notifications.start()
    reminder_loop.start()
    logger.info("Bot đã sẵn sàng nhận lệnh!")

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

    start_time = time.time()
    credentials = await user_manager.get_user_credentials(user_id) # Lấy thông tin đăng nhập từ file
    # Kiểm tra có thông tin dăng nhập chưa
    if credentials is None:
        print("Không có thông tin đăng nhập.")
        notifications = "Không có thông tin đăng nhập."
        return
    print(f"Đã tìm thấy thông tin đăng nhập: {time.time() - start_time:.2f} giây")
    
    notifications = get_notification_first_line()
    if notifications == "Không có thông tin đăng nhập":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh `/login` để đăng nhập.")
        return
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    elif notifications:
        await ctx.followup.send(f"**Thông báo mới nhất từ HUSC**:\n{notifications}")
    else:
        await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo.**")
    await user_manager.remember_request(user_id, ctx.user.name, "/first")

@bot.tree.command(name='remindall', description="Đặt lịch nhắc nhở")
async def remindall(interaction: discord.Interaction, reminder: str, day: int, month: int, year: int, hour: int, minute: int):    
    guild_id = interaction.guild.id if interaction.guild else "DM"
    if guild_id != "DM":
        guild = bot.get_guild(int(guild_id))
        if guild:
            logger.info(f"Nhắc nhở được tạo trong server: {guild.name} (ID: {guild_id})")
        else:
            logger.warning(f"Không tìm thấy server với ID: {guild_id}")
    write_remind_to_file(hour, minute, day, month, year, reminder, interaction.user.id, guild_id, interaction.channel.id)
    now = datetime.now(timezone)
    target_time = datetime(year, month, day, hour, minute)
    target_time = timezone.localize(target_time)
    if target_time < now:
        target_time = target_time.replace(year=now.year + 1)
    await interaction.response.defer()
    mesage = f"Đặt lời nhắc thành công vào {target_time.strftime('%d/%m/%Y %H:%M')}."
    logger.info(mesage)
    await interaction.followup.send(mesage)

@bot.tree.command(name="check", description="Kiểm tra trạng thái của bot")
async def check(ctx: discord.Interaction):
    await ctx.response.send_message("Bot đang hoạt động tốt!")

@tasks.loop(seconds=1)
async def reminder_loop():
    await check_reminders()

@tasks.loop(minutes=1)
async def send_notifications():
    global previous_notifications
    logger.info("=== Start loop get notifications ===")
    
    if os.path.exists('users.json'):
        with open('users.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = []
    if data:
        random_item = random.choice(data)
        random_id = random_item["id"]
        logging.info(f"ID ngẫu nhiên: {random_id}")
    else:
        logging.warning("Danh sách rỗng hoặc không có dữ liệu.")

    user_id = random_id
    if os.path.exists("notifications.txt"):
        with open("notifications.txt", "r", encoding="utf-8") as f:
            previous_notifications = f.read().strip() 
            previous_notifications = previous_notifications.lstrip('- ').strip()
    else:
        previous_notifications = None 
    logger.info("Đang tiến hành kiểm tra đăng nhập...")
    await husc_notification.check_login_id(user_id, user_manager)
    try:
        logger.info("Đang lấy thông báo...")
        task = asyncio.create_task(husc_notification.get_notifications(user_id, user_manager, auth_manager))
        notifications = await task 
        if isinstance(notifications, list) and notifications:
            new_notification = notifications[0] 
            if previous_notifications != new_notification and previous_notifications is not None:  
                formatted_notification = f"- {new_notification}"
                for guild in bot.guilds:
                    text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                    channel = text_channels[0] if text_channels else None
                    guild_info = {
                                'guild_name': guild.name,
                                'guild_id': str(guild.id),
                                'channel_name': channel.name,
                                'channel_id': str(channel.id),
                            }
                    guilds_info.append(guild_info)
                    if channel:
                        try:
                            await channel.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
                            logger.info(f"Đã gửi thông báo đến kênh: {channel.name} trong server: {guild.name}")
                        except discord.Forbidden:
                            logger.warning(f"Bot không có quyền gửi tin nhắn trong kênh: {channel.name} của server: {guild.name}")
                        except discord.HTTPException as e:
                            logger.error(f"Lỗi HTTP khi gửi tin nhắn đến kênh: {channel.name} của server: {guild.name}, chi tiết: {e}")
                with open("guilds_info.json", "w", encoding="utf-8") as f:
                    json.dump(guilds_info, f, ensure_ascii=False, indent=4)
                with open("notifications.txt", "w", encoding="utf-8") as f:
                    f.write(formatted_notification)
                previous_notifications = new_notification
            else:
                logger.info("Không có thông báo mới.")
        else:
            logger.info("Không thể lấy thông báo hoặc không có thông báo mới.")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

bot.run(bot_config.token)
