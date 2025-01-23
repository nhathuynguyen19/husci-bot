import asyncio, os, logging, discord, json, random, aiohttp, time
from config import logger, admin_id
from paths import users_path, notifications_path, guilds_info_path, unique_member_ids_path
from modules.utils.switch import switch
from modules.utils.file import load_json, save_json, save_txt
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
            previous_notifications = Nonek

        await self.user_manager.check_login_id(user_id)
        try:
            task = asyncio.create_task(self.husc_notification.get_notifications(user_id, self.user_manager, self.auth_manager))
            notifications = await task 
            if isinstance(notifications, list) and notifications:
                new_notification = notifications[0] 
                if previous_notifications != new_notification and previous_notifications is not None or previous_notifications == "Empty":
                    formatted_notification = f"- {new_notification}"

                    # gửi thông báo đến tất cả user trong tất cả server
                    users_data = await load_json(unique_member_ids_path)
                    for user in users_data['unique_members']:
                        if switch:
                            try:
                                await self.bot.get_user(int(user['id'])).send(f"**Thông báo mới nhất từ HUSC**:\n{formatted_notification}")
                                print(f"Đã gửi thông báo đến user: {user['username']}")
                            except discord.Forbidden:
                                logger.warning(f"Bot không thể gửi tin nhắn đến user: {user['username']}")
                            except discord.HTTPException as e:
                                logger.error(f"Lỗi HTTP khi gửi tin nhắn đến user: {user['username']}, chi tiết: {e}")
                        
                    with open("data/notifications.txt", "w", encoding="utf-8") as f:
                        f.writelines([f"- {notification}\n" for notification in notifications])
                    previous_notifications = new_notification
                else:
                    print("Không có thông báo mới")
            else:
                print("Không thể lấy thông báo hoặc không có thông báo mới")
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi trong vòng lặp thông báo: {e}")

    async def handle_update_guilds_info(self):
        guilds_info = []
        unique_members = {}

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id not in unique_members:
                    unique_members[member.id] = member.name

            guild_info = {
                'guild_name': guild.name,
                'guild_id': str(guild.id),
                'member_count': guild.member_count
            }
            guilds_info.append(guild_info)

        if os.path.exists(guilds_info_path):
            old_guilds_info = await load_json(guilds_info_path)
            if old_guilds_info != guilds_info:
                await save_json(guilds_info_path, guilds_info)
        else:
            await save_json(guilds_info_path, guilds_info)

        sorted_unique_members = sorted(
            [{'id': str(member_id), 'username': username} for member_id, username in unique_members.items()],
            key=lambda x: x['username'].lower()
        )
        
        data_members = {
            'total_unique_members': len(unique_members),
            'unique_members': sorted_unique_members
        }
        if os.path.exists(unique_member_ids_path):
            old_data = await load_json(unique_member_ids_path)
            if old_data != data_members:
                await save_json(unique_member_ids_path, data_members)
        else:
            await save_json(unique_member_ids_path, data_members)


