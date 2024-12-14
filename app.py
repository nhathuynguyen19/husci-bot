import discord, os, aiohttp
from discord.ext import commands, tasks
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Tải biến môi trường từ environment
load_dotenv()

# Lấy các giá trị từ môi trường
token = os.getenv("DISCORD_TOKEN")
login_id = os.getenv("LOGIN_ID")
password = os.getenv("PASSWORD")

# Kiểm tra xem có đầy đủ biến môi trường cần thiết không
if not all([token, login_id, password]):
    raise ValueError("Thiếu một hoặc nhiều biến môi trường cần thiết! Kiểm tra lại DISCORD_TOKEN, LOGIN_ID, PASSWORD.")

# trang web
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"

# Cấu hình bot với prefix là "/"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Hàm lấy thông báo từ trang web
async def get_notifications():
    try:
        async with aiohttp.ClientSession() as session:
            print("Đang truy cập trang đăng nhập...")
            login_page = await session.get(login_url)
            soup = BeautifulSoup(await login_page.text(), 'html.parser')
            
            token = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token:
                return "Không tìm thấy token xác thực!"

            print("Đang đăng nhập...")
            login_data = {
                "loginID": login_id, 
                "password": password, 
                "__RequestVerificationToken": token['value']
            }
            login_response = await session.post(login_url, data=login_data)
            if login_response.status != 200:
                return f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"

            print("Đang lấy thông báo...")
            data_response = await session.get(data_url)
            if data_response.status != 200:
                return f"Không thể lấy dữ liệu từ {data_url}. Mã lỗi: {data_response.status}"
            else:
                print("Lấy thông báo thành công.")
            
            soup = BeautifulSoup(await data_response.text(), 'html.parser')
            news_list = soup.find('div', id='newsList')
            if not news_list:
                return "Không tìm thấy danh sách thông báo!"

            notifications = [
                f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                for link in news_list.find_all('a', href=True) if '/News/Content' in link['href']
            ]
            if notifications:
                print(f"Đã lấy {len(notifications)} thông báo.");
            return notifications if notifications else "Không có thông báo mới."
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    await bot.tree.sync()  # Đồng bộ lệnh app_commands sau khi bot đã sẵn sàng
    send_notifications.start() # Bắt đầu vòng lặp gửi thông báo tự động
    print("Bot is ready and commands are synchronized.")

# Lệnh lấy 5 thông báo đầu
@bot.tree.command(name="notifications", description="Lấy thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
    
    notifications = await get_notifications()  # Gọi hàm lấy thông báo
    
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    else:
        top_notifications = notifications[:5]
        formatted_notifications = "\n".join([f"- {notification}" for notification in top_notifications])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")

# Lệnh lấy thông báo mới nhất
@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    await ctx.response.defer(ephemeral=False)  # defer cho phép bot gửi phản hồi sau
    
    notifications = await get_notifications()

    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    elif isinstance(notifications, list) and notifications:
        first_notification = notifications[0]
        formatted_notification = f"- {first_notification}"
        await ctx.followup.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
    else:
        await ctx.followup.send(f"**Đã xảy ra lỗi khi lấy thông báo.**")


# Biến lưu trữ thông báo trước đó
previous_notifications = []

@tasks.loop(minutes=5)
async def send_notifications():
    global previous_notifications

    notifications = await get_notifications()

    if isinstance(notifications, list) and notifications:
        new_notification = notifications[0]  # Lấy thông báo đầu tiên mới

        if previous_notifications != new_notification:  # So sánh thông báo mới với thông báo trước đó
            if previous_notifications: # nếu là lần đầu
                formatted_notification = f"- {new_notification}"

                guild = bot.guilds[0] if bot.guilds else None
                channel = guild.text_channels[0] if guild and guild.text_channels else None

                if channel:
                    await channel.send(f"**Thông báo mới từ HUSC**:\n{formatted_notification}")

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

# Chạy bot với token
bot.run(token)
