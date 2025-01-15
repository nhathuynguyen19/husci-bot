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
            reminders_set = await self.read_remind_from_file()
            modified = False

            # Xóa nhắc nhở cụ thể
            if reminder_element in reminders_set:
                reminders_set.remove(reminder_element)
                modified = True
                print(f"Nhắc nhở {reminder_element} đã được xóa.")
            else:
                print(f"Không tìm thấy nhắc nhở {reminder_element} trong danh sách.")

            # Kiểm tra từng nhắc nhở còn lại
            for reminder in reminders_set.copy():  # Duyệt bản sao để tránh lỗi khi xóa
                try:
                    parts = reminder.split(" - ")
                    date_time = parts[0]
                    date, time = date_time.split(" ")
                    day, month, year = map(int, date.split("-"))
                    hour, minute = map(int, time.split(":"))

                    # Kiểm tra ngày giờ hợp lệ
                    reminder_date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

                    # Kiểm tra nếu nhắc nhở đã quá hạn
                    if reminder_date < datetime.datetime.now():
                        logger.info(f"Nhắc nhở đã quá hạn: {reminder}")
                        reminders_set.remove(reminder)
                        modified = True

                except ValueError as e:  # Lỗi ngày tháng không hợp lệ
                    logger.error(f"Nhắc nhở không hợp lệ: {reminder}. Lỗi: {e}")
                    reminders_set.remove(reminder)
                    modified = True
                except Exception as e:
                    logger.error(f"Đã có lỗi xảy ra với nhắc nhở: {reminder}. Lỗi: {e}")

            # Chỉ lưu lại nếu danh sách đã thay đổi
            if modified:
                await self.save_reminders(reminders_set)
        except Exception as e:
            logger.error(f"Lỗi khi xóa nhắc nhở: {e}")

    async def check_reminders(self):
        now = datetime.now(timezone)
        now = now.replace(microsecond=0, tzinfo=None)
        reminders_set = await self.read_remind_from_file()

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
                    
                    await self.add_sent_reminder(reminder_line)
                    await self.remove_reminder(reminder_line)
            except Exception as e:
                logger.error(f"Lỗi khi xử lý nhắc nhở: {e}")

    async def write_remind_to_file(self, date_time, reminder, user_id, channel_id, guild_id):
        try:
            with open(self.reminders_path, 'a', encoding='utf-8') as file:
                reminder_time = datetime(date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute)
                file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
                print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
        except Exception as e:
            logger.error(f"Lỗi khi ghi nhắc nhở vào file: {e}")