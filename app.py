import discord
from discord.ext import tasks, commands
from datetime import datetime
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands, Reminder, Loops, Email
from paths  import sent_reminders_path, reminders_path, notifications_path, login_url, data_url
from colorama import init, Fore

# Objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(bot_config.fixed_key)
user_manager = UserManager()
husc_notification = HUSCNotifications(login_url, data_url[0], bot_config.fixed_key, notifications_path)
commands = Commands(husc_notification, user_manager, auth_manager)
reminders = Reminder(reminders_path, sent_reminders_path, bot)
loops = Loops(husc_notification, user_manager, auth_manager, bot)
email = Email(data_url[1], login_url)

# Initialize 
init(autoreset=True)
previous_notifications = None
guilds_info = []

# Commands
@bot.tree.command(name="login",description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    await commands.handle_login(ctx, username, password)
@bot.tree.command(name="notifications", description="Lấy các thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    await commands.handle_notifications(ctx)
@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    await commands.handle_first(ctx)
@bot.tree.command(name="remind", description="Đặt lịch nhắc nhở")
async def remind(ctx: discord.Interaction, reminder: str, day: int, month: int, year: int, hour: int, minute: int):   
    date_time = datetime(int(year), int(month), int(day), int(hour), int(minute))
    await commands.handle_remind(ctx, bot, reminder, reminders, date_time)
@bot.tree.command(name="message", description="Xem tin nhắn mới nhất")
async def message(ctx):
    await commands.handle_message(ctx)
    
# Loops
@tasks.loop(seconds=1)
async def one_second():
    await reminders.check_reminders()
@tasks.loop(minutes=1)
async def one_minute():
    global previous_notifications
    await loops.handle_auto_notifications(previous_notifications)
@tasks.loop(minutes=10)
async def ten_minutes():
    global guilds_info
    await loops.handle_update_guilds_info(guilds_info)
    await loops.handle_email(email)

# Events
@bot.event
async def on_ready():
    print(f'Truy cập bot thành công với tên: {Fore.GREEN}{bot.user}')
    await bot.tree.sync()
    print("Đã đồng bộ lệnh")
    one_second.start()
    one_minute.start()
    ten_minutes.start()
    print("Ready")

# Run
bot.run(bot_config.token)
