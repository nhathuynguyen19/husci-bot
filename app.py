import discord, os, aiohttp, json, html, base64
from discord.ext import commands, tasks
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
from config import fixed_key

# Tải biến môi trường từ environment
load_dotenv()

# Lấy các giá trị từ môi trường
token = os.getenv("DISCORD_TOKEN")

# Kiểm tra xem có đầy đủ biến môi trường cần thiết không
if not token:
    raise ValueError("Thiếu một hoặc nhiều biến môi trường cần thiết! Kiểm tra lại DISCORD_TOKEN, FIXED_KEY.")

# trang web
login_url = "https://student.husc.edu.vn/Account/Login"
data_url = "https://student.husc.edu.vn/News"

# Cấu hình bot với prefix là "/"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Mã hóa mật khẩu
def encrypt_password(password, discord_id, key):
    f = Fernet(key)
    # Kết hợp mật khẩu và ID Discord
    combined = f"{password}:{discord_id}"
    encrypted = f.encrypt(combined.encode())
    # Mã hóa mật khẩu thành base64 để lưu vào JSON
    encrypted_password_base64 = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_password_base64

# Giải mã mật khẩu
def decrypt_password(encrypted_password, discord_id, key):
     # Giải mã base64 trước
    encrypted_password_base64 = base64.b64decode(encrypted_password)
    
    # Tiến hành giải mã bằng Fernet
    f = Fernet(key)
    decrypted_combined = f.decrypt(encrypted_password_base64).decode()
    
    # Tách chuỗi thành mật khẩu và ID Discord
    password, original_discord_id = decrypted_combined.split(":")
    if int(original_discord_id) == discord_id:
        return password
    else:
        print("ID không khớp!")

# Định nghĩa hàm kiểm tra đăng nhập thành công
async def is_login_successful(login_response):
    # Lấy nội dung trang phản hồi
    page_content = await login_response.text()
    
    # Giải mã các ký tự HTML
    decoded_content = html.unescape(page_content)

    # Phân tích HTML bằng BeautifulSoup
    soup = BeautifulSoup(decoded_content, 'html.parser')

    # Kiểm tra nếu có span với class="text-danger" và chứa thông báo lỗi
    error_message = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')

    if error_message:
        print("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
        return False

    # Nếu không có thông báo lỗi, coi như đăng nhập thành công
    print("Đăng nhập thành công!")
    return True

# Hàm kiểm tra và lưu thông tin người dùng vào file JSON
def save_user_to_file(user, username=None, password=None):
    
    user_data = {
        "name": user.name,
        "id": user.id,
        "login_id": username,
        "password": password
    }

    try:
        # Đọc dữ liệu từ file JSON, hoặc khởi tạo mảng nếu file không tồn tại
        if os.path.exists("users.json"):
            with open("users.json", "r", encoding="utf-8") as file:
                content = file.read().strip()
                data = json.loads(content) if content else []
        else:
            data = []
    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file: {e}")
        data = []  # Nếu có lỗi, khởi tạo data là danh sách rỗng

    # Kiểm tra người dùng đã có trong danh sách chưa
    if any(existing_user["id"] == user.id for existing_user in data):
        return False  # Nếu người dùng đã có trong file, không cần lưu lại

    data.append(user_data)

    # Lưu thông tin vào file
    with open("users.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    return True

# Đọc user_id và lấy thông tin đăng nhập từ file user.json
def get_user_credentials(user_id):
    try:
        with open("users.json", "r", encoding="utf-8") as file:
            users = json.load(file)
            for user in users:
                if user["id"] == user_id:
                    return user  # Trả về tài khoản và mật khẩu
            return None  # Không tìm thấy user_id
    except FileNotFoundError:
        return None  # File không tồn tại

# Lệnh đăng nhập
@bot.tree.command(name="login", description="Lấy tài khoản đăng nhập HUSC")
async def login(ctx, username: str, password: str):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=True)
    
    async with aiohttp.ClientSession() as session:
        # Truy cập trang đăng nhập
        login_page = await session.get(login_url)
        soup = BeautifulSoup(await login_page.text(), 'html.parser')
        
        # Lấy token xác thực từ trang
        token = soup.find('input', {'name': '__RequestVerificationToken'})
        if not token:
            await ctx.followup.send("Không tìm thấy token xác thực!")
            return
        
        login_data = {
            "loginID": username,
            "password": password,
            "__RequestVerificationToken": token['value']
        }
        
        # Gửi yêu cầu đăng nhập
        login_response = await session.post(login_url, data=login_data)
        
        if not await is_login_successful(login_response):
            await ctx.followup.send("Tài khoản mật khẩu không chính xác! Hoặc bạn đã đăng nhập")
            return
        
        # mã hóa mật khẩu để lưu
        password = encrypt_password(password, user_id, fixed_key)
        
         # Lưu thông tin người dùng vào file
        success = save_user_to_file(ctx.user, username, password)
        if success:
            await ctx.followup.send(f"Đăng nhập thành công cho người dùng {ctx.user.name}.")
        else:
            await ctx.followup.send("Tài khoản đã tồn tại. Bạn đã đăng nhập rồi.")
        
# Hàm lấy thông báo từ trang web
async def get_notifications(user_id):
    
    # Lấy thông tin đăng nhập từ file
    credentials = get_user_credentials(user_id)
    
    # kiểm tra có thông tin dăng nhập chưa
    if credentials is None:
        return "Không có thông tin đăng nhập"  # Không tìm thấy thông tin đăng nhập

    # lấy thông tin đăng nhập người dùng gọi lệnh
    login_id, password = credentials['login_id'], credentials['password']
    
    # giải mã mật khẩu
    password = decrypt_password(password, user_id, fixed_key)
    
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
            ][:5]
            
            if notifications:
                print(f"Đã lấy {len(notifications)} thông báo.")
            return notifications if notifications else "Không có thông báo mới."
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

# Sự kiện khi bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập thành công với tên: {bot.user}')
    await bot.tree.sync()  # Đồng bộ lệnh app_commands sau khi bot đã sẵn sàng
    # send_notifications.start() # Bắt đầu vòng lặp gửi thông báo tự động
    print("Bot is ready and commands are synchronized.")







# Lệnh lấy 5 thông báo đầu
@bot.tree.command(name="notifications", description="Lấy thông báo mới từ HUSC")
async def notifications(ctx: discord.Interaction):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
    
    notifications = await get_notifications(user_id)  # Gọi hàm lấy thông báo
    
    if notifications == "Không có thông tin đăng nhập":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh /login để đăng nhập.")
        return
    
    if notifications == "Không có thông báo mới.":
        await ctx.followup.send(f"**Không có thông báo mới.**")
    else:
        top_notifications = notifications[:5]
        formatted_notifications = "\n".join([f"- {notification}" for notification in top_notifications])
        await ctx.followup.send(f"**Các thông báo mới từ HUSC**:\n{formatted_notifications}")

# Lệnh lấy thông báo mới nhất
@bot.tree.command(name="first", description="Lấy thông báo mới nhất từ HUSC")
async def first(ctx: discord.Interaction):
    # Lấy ID người viết lệnh
    user_id = ctx.user.id
    
    # Đảm bảo defer để bot không bị timeout khi chờ phản hồi lâu
    if not ctx.response.is_done():
        await ctx.response.defer(ephemeral=False)
        
    notifications = await get_notifications(user_id)  # Gọi hàm lấy thông báo
    
    if notifications == "Không có thông tin đăng nhập":
        await ctx.followup.send("Chưa đăng nhập tài khoản HUSC! Dùng lệnh /login để đăng nhập.")
        return


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

# lệnh tự động thông báo mỗi khi có thông báo mới
@tasks.loop(minutes=30)
async def send_notifications():
    global previous_notifications
    try:
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
    except Exception as e:
        print(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

# Chạy bot với token
bot.run(token)
