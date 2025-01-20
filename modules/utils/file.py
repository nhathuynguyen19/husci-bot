from config import logger
import asyncio, os, datetime, json, unicodedata, markdown
from paths import sent_reminders_path, reminders_path

# html
# md to html
async def md_to_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()
    html_content = markdown.markdown(md_content)
    return html_content
# save html
async def save_html(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"Dữ liệu đã được lưu thành công vào {file_path}")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi lưu dữ liệu: {e}")
        
# md
# save
async def save_md(file_path, data):
    """Lưu dữ liệu vào file MD dưới dạng văn bản thuần túy."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"Dữ liệu đã được lưu thành công vào {file_path}")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi lưu dữ liệu: {e}")
# load
async def load_md(file_path):
    try:
        # Kiểm tra nếu tệp tồn tại
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        else:
            print(f"Không tìm thấy tệp tại đường dẫn: {file_path}")
            return None
    except Exception as e:
        print(f"Đã xảy ra lỗi khi tải tệp: {e}")
        return None
        
# str
async def remove_accents(input_str):
    normalized_str = unicodedata.normalize('NFD', input_str)
    filtered_str = ''.join(c for c in normalized_str if unicodedata.category(c) != 'Mn')
    return filtered_str

# json
# load
async def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                logger.error(f"File '{path}' không hợp lệ. Trả về danh sách rỗng")
                return []
    else:
        logger.warning(f"Tệp {path} không tồn tại. Tạo tệp mới.")
        with open(path, 'w', encoding='utf-8') as f:
            f.write('[]')
        return []
# save
async def save_json(file_path, data):
    """Lưu dữ liệu vào file JSON."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Dữ liệu đã được lưu thành công vào {file_path}")
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi lưu dữ liệu: {e}")

# txt
# load
async def load_txt(path):
    try:
        if not os.path.exists(path):
            logger.warning(f"Tệp {path} không tồn tại. Tạo tệp mới.")
            with open(path, 'w', encoding='utf-8') as f:
                pass
            return set() 
        with open(path, 'r', encoding='utf-8') as f:
            content = {line.strip() for line in f}
        return content
    except Exception as e:
        logger.error(f"Lỗi khi đọc tệp {path}: {e}")
        return set()
# save
async def save_txt(txt_set, path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            for element in txt_set:
                f.write(f"{element}\n")
        print(f"Dữ liệu đã lưu vào {path}")
    except Exception as e:
        logger.error(f"Lỗi khi ghi vào tệp {path}: {e}")

# sent_reminders.txt
# add
async def add_sent_reminder(reminder_line):
    sent_reminders_set = await load_txt(sent_reminders_path)
    if not isinstance(sent_reminders_set, set):
        sent_reminders_set = set(sent_reminders_set)
    if reminder_line not in sent_reminders_set:
        sent_reminders_set.add(reminder_line)
        await save_txt(sent_reminders_set, sent_reminders_path)

# reminders.txt
# add
async def add_reminder(date_time, reminder, user_id, channel_id, guild_id):
    try:
        with open(reminders_path, 'a', encoding='utf-8') as file:
            reminder_time = datetime(date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute)
            file.write(f"{reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}\n")
            print(f"Đã lưu nhắc nhở: {reminder_time} - {reminder} - {user_id} - {guild_id} - {channel_id}")
    except Exception as e:
        logger.error(f"Lỗi khi ghi nhắc nhở vào file: {e}")
# remove
async def remove_reminder(reminder_element):
    try:
        reminders_set = await load_txt(reminders_path)
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
            await save_txt(reminders_set, reminders_path)
    except Exception as e:
        logger.error(f"Lỗi khi xóa nhắc nhở: {e}")