from config import logger
import asyncio, pytz, discord, aiohttp, os
from datetime import datetime
from pytz import timezone

timezone = pytz.timezone('Asia/Ho_Chi_Minh')

class Reminder:
    def __init__(self, reminders_path, sent_reminder_path, bot):
        self.reminders_path = reminders_path
        self.sent_reminders_path = sent_reminder_path
        self.bot = bot

    async def load_sent_reminders(self):
        try:
            if not os.path.exists(self.sent_reminders_path):  # Kiểm tra xem tệp có tồn tại không
                logger.warning(f"Tệp {self.sent_reminders_path} không tồn tại. Tạo tệp mới.")
                # Tạo tệp mới nếu không tồn tại
                with open(self.sent_reminders_path, 'w', encoding='utf-8') as f:
                    pass  # Tạo tệp rỗng
                return set()  # Trả về tập hợp rỗng nếu tệp không có dữ liệu

            with open(self.sent_reminders_path, 'r', encoding='utf-8') as f:
                sent_reminders = {line.strip() for line in f}
            return sent_reminders
        except Exception as e:
            logger.error(f"Lỗi khi đọc tệp {self.sent_reminders_path}: {e}")
            return set()

    async def save_sent_reminders(self, sent_reminders_set):
        try:
            with open(self.sent_reminders_path, 'w', encoding='utf-8') as f:
                for reminder in sent_reminders_set:
                    f.write(f"{reminder}\n")
            print(f"Nhắc nhở đã được lưu vào tệp {self.sent_reminders_path}")
        except Exception as e:
            logger.error(f"Lỗi khi ghi vào tệp {self.sent_reminders_path}: {e}")

    async def add_sent_reminder(self, reminder_line):
        sent_reminders_set = await self.load_sent_reminders()
        if not isinstance(sent_reminders_set, set):
            sent_reminders_set = set(sent_reminders_set)
        if reminder_line not in sent_reminders_set:
            sent_reminders_set.add(reminder_line)
            await self.save_sent_reminders(sent_reminders_set)

    async def read_remind_from_file(self):
        try:
            if not os.path.exists(self.reminders_path):
                logger.warning(f"Tệp {self.reminders_path} không tồn tại. Tạo tệp mới.")
                with open(self.reminders_path, 'w', encoding='utf-8') as f:
                    pass
                return set()
            
            with open(self.reminders_path, 'r', encoding='utf-8') as f:
                reminders = {line.strip() for line in f}
            return reminders
        except Exception as e:
            logger.error(f"Lỗi khi đọc tệp {self.reminders_path}: {e}")
            return set()
        
    # Lưu nhắc nhở mới vào file
    async def save_reminders(self, reminders_set):
        try:
            with open(self.reminders_path, 'w', encoding='utf-8') as f:
                for reminder in reminders_set:
                    f.write(f"{reminder}\n")
            print(f"Nhắc nhở đã được lưu vào tệp {self.reminders_path}")
        except Exception as e:
            logger.error(f"Lỗi khi ghi vào tệp {self.reminders_path}: {e}")

    async def remove_reminder(self, reminder_element):
        try:
            # Đọc danh sách nhắc nhở đã lưu từ file
            reminders_set = await self.read_remind_from_file()

            # Nếu nhắc nhở cần xóa có trong danh sách, xóa nó
            if reminder_element in reminders_set:
                reminders_set.remove(reminder_element)
                # Cập nhật lại file với danh sách nhắc nhở mới
                await self.save_reminders(reminders_set)
                print(f"Nhắc nhở {reminder_element} đã được xóa.")
            else:
                print(f"Không tìm thấy nhắc nhở {reminder_element} trong danh sách.")
        except Exception as e:
            logger.error(f"Lỗi khi xóa nhắc nhở: {e}")

    async def check_reminders(self):
        now = datetime.now(timezone)
        if now.tzinfo is None: 
            now = timezone.localize(now) 
        reminders_set = await self.read_remind_from_file() 
        sent_reminders_set = await self.load_sent_reminders()
        for reminder_line in reminders_set:
            try:
                reminder_parts = reminder_line.strip().split(' - ', 4)
                if len(reminder_parts) < 5:
                    logger.error(f"Lỗi: Nhắc nhở không hợp lệ: {reminder_line}")
                    continue
                reminder_time_str = reminder_parts[0]
                reminder_msg = reminder_parts[1]
                user_id = int(reminder_parts[2])
                channel_id = int(reminder_parts[4])
                # Xử lý thời gian nhắc nhở với định dạng đúng
                try:
                    reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%d %H:%M')
                    reminder_time = timezone.localize(reminder_time)
                except ValueError:
                    logger.error(f"Lỗi: Nhắc nhở với thời gian không hợp lệ: {reminder_time_str}")
                    continue  # Bỏ qua nhắc nhở này nếu thời gian không hợp lệ

                time_diff = abs((reminder_time - now).total_seconds())
                if time_diff < 1: 
                    reminder_element = f"{reminder_time} - {reminder_msg} - {user_id} - {channel_id}"
                    if reminder_element in sent_reminders_set:
                        print(f"Nhắc nhở đã được gửi trước đó.")
                        continue
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
                    await self.add_sent_reminder(reminder_element)
                    await self.remove_reminder(reminder_line)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")

    async def write_remind_to_file(self, hour, minute, day, month, year, reminder, user_id, channel_id, guild_id):
        try:
            with open(self.reminders_path, 'a', encoding='utf-8') as file:
                reminder_time = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
                file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
                print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
        except Exception as e:
            logger.error(f"Lỗi khi ghi nhắc nhở vào file: {e}")