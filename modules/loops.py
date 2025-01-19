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
            random_id = random_item.get("id")
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

