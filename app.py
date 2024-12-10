import discord
from discord.ext import commands
import os
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

if token is None:
    raise ValueError("Không tìm thấy token Discord! Vui lòng kiểm tra lại biến môi trường DISCORD_TOKEN.")

# Tạo bot với prefix lệnh, ví dụ: "/"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# URL đăng nhập và URL dữ liệu cần lấy
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/Message/Inbox"

# Tạo session bất đồng bộ với aiohttp
async def get_notifications():
    try:
        async with aiohttp.ClientSession() as session:
            # Lấy trang đăng nhập để lấy token xác thực
            async with session.get(login_url) as login_page:
                soup = BeautifulSoup(await login_page.text(), 'html.parser')

            # Lấy token __RequestVerificationToken từ trang đăng nhập
            token = soup.find('input', {'name': '__RequestVerificationToken'})['value']

            # Dữ liệu đăng nhập
            login_data = {
                "loginID": "23T1080025",  # Thay bằng mã sinh viên của mày
                "password": "16082005159487!Hh",  # Thay bằng mật khẩu
                "__RequestVerificationToken": token  # Token xác thực
            }

            # Gửi yêu cầu đăng nhập
            async with session.post(login_url, data=login_data) as login_response:
                if login_response.status == 200:
                    # Lấy dữ liệu từ trang sau khi đăng nhập
                    async with session.get(data_url) as data_response:
                        if data_response.status == 200:
                            # Phân tích nội dung trang
                            soup = BeautifulSoup(await data_response.text(), 'html.parser')
                            
                            # Tìm tất cả các thẻ <a> có href chứa '/News/Content/'
                            links = soup.find_all('a', href=True)
                            
                            notifications = []
                            for link in links:
                                if '/News/Content/' in link['href']:
                                    notifications.append(link.text.strip())
                            
                            if not notifications:
                                return "Không có thông báo mới."
                            return "\n".join(notifications)
                        else:
                            return f"Không thể lấy dữ liệu từ {data_url}. Mã lỗi: {data_response.status}"
                else:
                    return "Đăng nhập không thành công."
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Đã đăng nhập thành công với bot: {bot.user}')

# Lệnh "/notifications" để lấy thông báo
@bot.command(name="notifications")
async def fetch_notifications(ctx):
    await ctx.send("Đang lấy thông báo từ HUSC...")
    notifications = await get_notifications()  # Đảm bảo gọi async function
    await ctx.send(notifications)

# Chạy bot với token
bot.run(token)
