import asyncio, os, logging, discord, json, random, aiohttp, time
from config import logger
from paths import users_path, notifications_path, guilds_info_path
from switch import switch
from modules.utils.file import load_json, save_json
from modules.utils.http import login_page


class Loops:
    def __init__(self, husc_notification, user_manager, auth_manager, bot):
        self.login_url = husc_notification.login_url
        self.husc_notification = husc_notification
        self.user_manager = user_manager
        self.auth_manager = auth_manager
        self.bot = bot

    async def handle_auto_notifications(self, previous_notifications):
        print("\nSTART AUTO GET NOTIFICATIONS")
        
        if os.path.exists(users_path):
            with open(users_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = []
        if data:
            random_item = random.choice(data)
            random_id = random_item["id"]
            print(f"ID ngẫu nhiên: {random_id}")
        else:
            logging.warning("Danh sách rỗng hoặc không có dữ liệu.")

        user_id = random_id

        if os.path.exists(notifications_path):
            notifications = await self.husc_notification.read_notifications()
            if notifications:
                previous_notifications = notifications[0].lstrip('- ').strip()
            else:
                previous_notifications = "Empty" 
        else:
            previous_notifications = None

        await self.user_manager.check_login_id(user_id)
        try:
            task = asyncio.create_task(self.husc_notification.get_notifications(user_id, self.user_manager, self.auth_manager))
            notifications = await task 
            if isinstance(notifications, list) and notifications:
                new_notification = notifications[0] 
                if previous_notifications != new_notification and previous_notifications is not None or previous_notifications == "Empty":
                    formatted_notification = f"- {new_notification}"
                    for guild in self.bot.guilds:
                        text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                        channel = text_channels[0] if text_channels else None
                        if channel and switch:
                            try:
                                await channel.send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
                                print(f"Đã gửi thông báo đến kênh: {channel.name} trong server: {guild.name}")
                            except discord.Forbidden:
                                logger.warning(f"Bot không có quyền gửi tin nhắn trong kênh: {channel.name} của server: {guild.name}")
                            except discord.HTTPException as e:
                                logger.error(f"Lỗi HTTP khi gửi tin nhắn đến kênh: {channel.name} của server: {guild.name}, chi tiết: {e}")
                    with open("data/notifications.txt", "w", encoding="utf-8") as f:
                        f.writelines([f"- {notification}\n" for notification in notifications])
                    previous_notifications = new_notification
                else:
                    print("Không có thông báo mới")
            else:
                print("Không thể lấy thông báo hoặc không có thông báo mới")
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

    async def handle_update_guilds_info(self, guilds_info):
        for guild in self.bot.guilds:
            text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
            channel = text_channels[0] if text_channels else None
            guild_info = {
                'guild_name': guild.name,
                'guild_id': str(guild.id),
                'channel_name': channel.name,
                'channel_id': str(channel.id),
                'member_count': guild.member_count
            }
            guilds_info.append(guild_info)
        with open(guilds_info_path, "w", encoding="utf-8") as f:
            json.dump(guilds_info, f, ensure_ascii=False, indent=4)

    async def handle_email(self, email_object):
        # Đọc dữ liệu người dùng từ JSON
        users_data = await load_json(users_path)
        tasks = []
        results = []
        
        for user in users_data:
            login_id, encrypted_password = user.get("login_id"), user.get("password")
            start_time = time.time()
            password = await self.auth_manager.decrypt_password(encrypted_password, user.get("id"), start_time)

            # Tạo một session riêng cho mỗi người dùng
            async with aiohttp.ClientSession() as session:  # Tạo session riêng cho mỗi user
                task = asyncio.create_task(email_object.fetch_data(session, login_id, password))  # Truyền session vào fetch_data
                tasks.append((user, task))
                print(f"Session for {login_id}: {session}")
                # Chờ các tác vụ hoàn thành
                completed_tasks = await asyncio.gather(*[task for _, task in tasks])

        # Sau khi tất cả các tác vụ hoàn thành, xử lý kết quả
        for (user, result) in zip([user for user, _ in tasks], completed_tasks):
            latest_email = result
            if "sms" not in user:
                user["sms"] = latest_email
            else:
                if user["sms"] != latest_email:
                    new_login = user["sms"]
                    user["sms"] = latest_email
                    user_id = user['id']
                    user = await self.bot.fetch_user(int(user_id))  
                    if user and new_login != "":
                        await user.send(f"**Tin nhắn mới**:\n{latest_email}")
                        print(f"Tin nhắn mới đã gửi đến {user_id}: {latest_email}")
                    else:
                        logger.warning(f"Không tìm thấy người dùng với ID: {user_id}")
                    
            if isinstance(user, dict) and "login_id" in user:
                results.append({
                    "login_id": user["login_id"],
                    "sms": user.get("sms", "")  # Mặc định trả về None nếu không có key "sms"
                })
            else:
                logger.warning(f"Dữ liệu user không hợp lệ: {user}")

        await save_json(users_path, users_data)
        return results
