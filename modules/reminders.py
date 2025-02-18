from config import logger
import asyncio, pytz, discord, aiohttp, os
from datetime import datetime
from pytz import timezone
from modules.utils.file import add_sent_reminder, remove_reminder, load_txt
from paths import reminders_path
from paths import BASE_DIR

timezone = pytz.timezone('Asia/Ho_Chi_Minh')

class Reminder:
    def __init__(self, reminders_path, sent_reminder_path, bot):
        self.reminders_path = reminders_path
        self.sent_reminders_path = sent_reminder_path
        self.bot = bot

    async def check_reminders(self):
        now = datetime.now(timezone)
        now = now.replace(microsecond=0, tzinfo=None)
        reminders_set = await load_txt(reminders_path)

        for reminder_line in reminders_set:
            try:
                reminder_parts = reminder_line.strip().split(' - ', 4)
                if len(reminder_parts) < 5:
                    logger.error(f"Lỗi: Nhắc nhở không hợp lệ: {reminder_line}")
                    continue

                reminder_time, reminder_msg, user_id_str, _, channel_id_str = reminder_parts
                date, time = reminder_time.split(' ')
                year, month, day = map(int, date.split('-'))
                hour, minute, second = map(int, time.split(':'))
                reminder_time = datetime(year, month, day, hour, minute, second)
                # Gửi nhắc nhở
                user_id = int(user_id_str)
                channel_id = int(channel_id_str)
                diff = (reminder_time - now).total_seconds()
                if diff <= 0:
                    if diff >= -1:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(f"<@{user_id}> Nhắc nhở: {reminder_msg}")
                            print(f"Nhắc nhở gửi đến kênh {channel_id}: {reminder_msg}")
                        else:
                            logger.warning(f"Không tìm thấy kênh với ID: {channel_id}")

                        user = await self.bot.fetch_user(user_id)  
                        if user:
                            await user.send(f"Nhắc nhở: {reminder_msg}")
                            print(f"Nhắc nhở gửi đến người dùng {user_id}: {reminder_msg}")
                        else:
                            logger.warning(f"Không tìm thấy người dùng với ID: {user_id}")
                    
                    await add_sent_reminder(reminder_line)
                    await remove_reminder(reminder_line)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")