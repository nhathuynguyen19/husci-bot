import discord
from discord.ext import commands
from discord import app_commands
import os
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Tải biến môi trường từ file .env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
login_id = os.getenv("LOGIN_ID")
password = os.getenv("PASSWORD")

if token is None or login_id is None or password is None:
    raise ValueError("Không tìm thấy các biến môi trường cần thiết! Vui lòng kiểm tra lại DISCORD_TOKEN, LOGIN_ID và PASSWORD.")

# Cấu hình bot với prefix là "/"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# URL đăng nhập và URL dữ liệu cần lấy
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/Message/Inbox"

# Hàm lấy thông báo từ trang web
async def get_notifications():
    try:
        async with aiohttp.ClientSession() as session:
            # Lấy trang đăng nhập để lấy token xác thực
            async with session.get(login_url) as login_page:
                soup = BeautifulSoup(await login_page.text(), 'html.parser')

            # Lấy token __RequestVerificationToken từ trang đăng nhập
            token = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token:
                return "Không tìm thấy token xác thực!"

            token_value = token['value']

            # Dữ liệu đăng nhập
            login_data = {
                "loginID": login_id,  # Sử dụng biến môi trường
                "password": password,  # Sử dụng biến môi trường
                "__RequestVerificationToken": token_value
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
                    return f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    await bot.tree.sync()  # Đồng bộ lệnh app_commands sau khi bot đã sẵn sàng

@bot.tree.command(name="notifications", description="Lấy thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    # Báo cho người dùng biết rằng bot đang xử lý
    await ctx.response.defer(ephemeral=False)  # defer cho phép bot gửi phản hồi sau
    
    notifications = await get_notifications()  # Gọi hàm lấy thông báo
    
    # Kiểm tra nếu có thông báo và trả lại chúng
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")  # Sử dụng followup để trả lời sau defer
    else:
        # Nếu có thông báo, hiển thị chúng dưới dạng danh sách
        formatted_notifications = "\n".join([f"- **{notification}**" for notification in notifications.splitlines()])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")


# Chạy bot với token
bot.run(token)
