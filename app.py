import os, json, time, random, logging, asyncio, html, base64, discord, aiohttp, pytz, lxml
from cryptography.fernet import Fernet
from discord.ext         import tasks, commands
from datetime            import datetime
from colorama            import init, Fore
from modules             import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands, Reminder, Loops
from config              import admin_id, logger
from dotenv              import load_dotenv
from paths               import sent_reminders_path, reminders_path, notifications_path, login_url, data_url, users_path
from pytz                import timezone
from bs4                 import BeautifulSoup

# Objects
bot_config        = BotConfig() 
bot               = bot_config.create_bot()
auth_manager      = AuthManager(bot_config.fixed_key)
user_manager      = UserManager()
husc_notification = HUSCNotifications(login_url, data_url[0], bot_config.fixed_key, notifications_path)
commands          = Commands(husc_notification, user_manager, auth_manager)
reminders         = Reminder(reminders_path, sent_reminders_path, bot)
loops             = Loops(husc_notification, user_manager, auth_manager, bot)

# Initialize 
init(autoreset = True)
timezone               = pytz.timezone('Asia/Ho_Chi_Minh')
previous_notifications = None
guilds_info            = []

@bot.tree.command(name="login", description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    await commands.handle_login(ctx, username, password)

@bot.tree.command(name="notifications", description="Lấy các thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    await commands.handle_notifications(ctx)

@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    await commands.handle_first(ctx)

@bot.tree.command(name='remind', description="Đặt lịch nhắc nhở")
async def remind(ctx: discord.Interaction, reminder: str, day: int, month: int, year: int, hour: int, minute: int):   
    date_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
    await commands.handle_remind(ctx, bot, reminder, reminders, date_time)
    
@tasks.loop(seconds=1)
async def reminder_loop():
    await reminders.check_reminders()

@tasks.loop(minutes=1)
async def auto_notifications():
    global previous_notifications
    await loops.handle_auto_notifications(previous_notifications)

@tasks.loop(minutes=10)
async def update_guilds_info():
    global guilds_info
    await loops.handle_update_guilds_info(guilds_info)

@bot.event
async def on_ready():
    print(f'Truy cập bot thành công với tên: {bot.user}')
    await bot.tree.sync()
    print("Đã đồng bộ lệnh")
    auto_notifications.start()
    reminder_loop.start()
    update_guilds_info.start()
    print("Ready")

bot.run(bot_config.token)
