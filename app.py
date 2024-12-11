import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime, timedelta

# Tải biến môi trường từ file .env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
login_id = os.getenv("LOGIN_ID")
password = os.getenv("PASSWORD")
channel_id = os.getenv("DISCORD_CHANNEL_ID")  # Thêm biến môi trường cho Channel ID

if token is None or login_id is None or password is None or channel_id is None:
    raise ValueError("Không tìm thấy các biến môi trường cần thiết! Vui lòng kiểm tra lại DISCORD_TOKEN, LOGIN_ID, PASSWORD và DISCORD_CHANNEL_ID.")

# Cấu hình bot với prefix là "/"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# URL đăng nhập và URL dữ liệu cần lấy
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/Message/Inbox"

# Biến lưu trữ thông báo trước đó
previous_notifications = []

# Hàm lấy thông báo từ trang web
async def get_notifications():
    try:
        async with aiohttp.ClientSession() as session:
            # Lấy token xác thực từ trang đăng nhập
            login_page = await session.get(login_url)
            soup = BeautifulSoup(await login_page.text(), 'html.parser')
            token = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token:
                return "Không tìm thấy token xác thực!"
            
            # Đăng nhập và lấy dữ liệu thông báo
            login_data = {
                "loginID": login_id, "password": password, "__RequestVerificationToken": token['value']
            }
            login_response = await session.post(login_url, data=login_data)
            if login_response.status != 200:
                return f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"
            
            # Lấy dữ liệu thông báo sau khi đăng nhập
            data_response = await session.get(data_url)
            if data_response.status != 200:
                return f"Không thể lấy dữ liệu từ {data_url}. Mã lỗi: {data_response.status}"
            
            # Phân tích và lấy thông báo
            soup = BeautifulSoup(await data_response.text(), 'html.parser')
            links = soup.find_all('a', href=True)
            notifications = [
                f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                for link in links if '/News/Content/' in link['href']
            ]
            
            return notifications if notifications else "Không có thông báo mới."
    
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

      
# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    await bot.tree.sync()  # Đồng bộ lệnh app_commands sau khi bot đã sẵn sàng
    send_notifications.start() # Bắt đầu vòng lặp gửi thông báo tự động
    
@bot.tree.command(name="notifications", description="Lấy thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    # Báo cho người dùng biết rằng bot đang xử lý
    await ctx.response.defer(ephemeral=True)  # defer cho phép bot gửi phản hồi sau
    
    notifications = await get_notifications()  # Gọi hàm lấy thông báo
    
    # Kiểm tra nếu có thông báo và trả lại chúng
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")  # Sử dụng followup để trả lời sau defer
    else:
        # Nếu có thông báo, hiển thị chúng dưới dạng danh sách với link
        formatted_notifications = "\n".join([f"- {notification}" for notification in notifications.splitlines()])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")
        
from discord.ext import tasks

# Biến lưu trữ thông báo trước đó
previous_notifications = []

@tasks.loop(minutes=5)
async def send_notifications():
    global previous_notifications

    # Lấy thông báo mới
    notifications = await get_notifications()  # gọi hàm lấy thông báo

    # Nếu thông báo là một danh sách, thì xử lý
    if isinstance(notifications, list):
        formatted_notifications = "\n".join([f"- {notification}" for notification in notifications])

        # So sánh với thông báo trước đó
        if notifications != previous_notifications:
            # Lưu thông báo vào file .txt
            with open('notifications.txt', 'w', encoding='utf-8') as f:
                f.write(f"**Thông báo mới từ HUSC**:\n{formatted_notifications}")

            # Gửi thông báo vào Discord
            channel = bot.get_channel(int(channel_id))  # Lấy channel từ ID
            if channel:
                await channel.send(f"**Thông báo mới từ HUSC**:\n{formatted_notifications}")

            # Cập nhật thông báo trước đó
            previous_notifications = notifications
        else:
            print("Không có thông báo mới hoặc thông báo không thay đổi.")
    else:
        # Nếu không có thông báo mới
        channel = bot.get_channel(int(channel_id))  # Lấy channel từ ID
        if channel:
            await channel.send(f"**Không có thông báo mới.**")

# Đảm bảo bắt đầu vòng lặp khi bot sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    send_notifications.start()  # Bắt đầu vòng lặp gửi thông báo tự động
    

# Chạy bot với token
bot.run(token)
