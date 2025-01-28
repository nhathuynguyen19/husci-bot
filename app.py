import discord, subprocess
from discord.ext import tasks, commands
from datetime import datetime
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications, Commands, Reminder, Loops, EmailsHandler
from paths  import sent_reminders_path, guilds_info_path, reminders_path, notifications_path, login_url, data_url, users_path, unique_member_ids_path, path_creator, bot_log_path
from colorama import init, Fore
from modules.utils.http import handle_users

# Objects
bot_config = BotConfig() 
bot = bot_config.create_bot()
auth_manager = AuthManager(bot_config.fixed_key)
user_manager = UserManager(users_path)
husc_notification = HUSCNotifications(login_url, data_url[0], bot_config.fixed_key, notifications_path)
reminders = Reminder(reminders_path, sent_reminders_path, bot)
loops = Loops(husc_notification, user_manager, auth_manager, bot)
emails_handler = EmailsHandler(auth_manager, bot, users_path)
commands = Commands(husc_notification, user_manager, auth_manager, loops, emails_handler)

# Initialize 
init(autoreset=True)
previous_notifications = None

# tạo các đường dẫn
try:
    path_creator(bot_log_path)
    path_creator(sent_reminders_path)
    path_creator(reminders_path)
    path_creator(notifications_path)
    path_creator(users_path)
    path_creator(guilds_info_path)
    path_creator(unique_member_ids_path)
except Exception as e:
    print(f"Error creating path: {e}")

# Commands
@bot.tree.command(name="login",description="Đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    await commands.handle_login(ctx, username, password)
@bot.tree.command(name="logout", description="Đăng xuất")
async def login(ctx):
    await commands.handle_logout(ctx)
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
@bot.tree.command(name="lastscore", description="Xem lại cập nhật điểm lần cuối")
async def last_score(ctx):
    await commands.handle_last_score(ctx, bot)
@bot.tree.command(name="scoretable", description="Xem bảng điểm")
async def full_score(ctx):
    await commands.handle_full_score(ctx, bot)
    
# Loops
@tasks.loop(seconds=1)
async def one_second():
    await reminders.check_reminders()
    await loops.handle_update_guilds_info()
@tasks.loop(minutes=1)
async def one_minute():
    global previous_notifications
    await loops.handle_auto_notifications(previous_notifications)

# Events
@bot.event
async def on_ready():
    print(f'{Fore.GREEN}{bot.user} {Fore.WHITE}đang đồng bộ lệnh')
    await bot.tree.sync()
    
    print("Đã đồng bộ lệnh")
    one_second.start()
    one_minute.start()
    print("Ready")
    
    # init
    await handle_users(auth_manager, bot, emails_handler)
    
# Run
bot.run(bot_config.token)
