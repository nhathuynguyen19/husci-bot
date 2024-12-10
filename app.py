import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

# Tạo bot với prefix lệnh, ví dụ: "!"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# URL đăng nhập và URL dữ liệu cần lấy
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/Message/Inbox"

# Tạo session để duy trì trạng thái đăng nhập
session = requests.Session()

def get_notifications():
    try:
        # Lấy trang đăng nhập để lấy token xác thực
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.text, 'html.parser')

        # Lấy token __RequestVerificationToken từ trang đăng nhập
        token = soup.find('input', {'name': '__RequestVerificationToken'})['value']

        # Dữ liệu đăng nhập
        login_data = {
            "loginID": "23T1080025",  # Thay bằng mã sinh viên của mày
            "password": "16082005159487!Hh",  # Thay bằng mật khẩu
            "__RequestVerificationToken": token  # Token xác thực
        }

        # Gửi yêu cầu đăng nhập
        login_response = session.post(login_url, data=login_data)

        if login_response.status_code == 200:
            # Lấy dữ liệu từ trang sau khi đăng nhập
            data_response = session.get(data_url)
            if data_response.status_code == 200:
                # Phân tích nội dung trang
                soup = BeautifulSoup(data_response.text, 'html.parser')
                
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
                return f"Không thể lấy dữ liệu từ {data_url}. Mã lỗi: {data_response.status_code}"
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
    notifications = get_notifications()
    await ctx.send(notifications)

# Thay 'your_bot_token_here' bằng token bot của mày
bot.run('MTMxNjA1NDk1NTc0ODIyOTIzMQ.Gdo-h7.9-jTWRzH6V4JnmGNuV9lbAjOyXsc8K_QovPg88')
