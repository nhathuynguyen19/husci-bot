import aiohttp, time, asyncio, os, unicodedata, discord
from bs4 import BeautifulSoup
from config import logger, convert_to_acronym
from modules.utils.file import save_txt, load_json, save_json, remove_accents, save_md, load_md
from paths import temp_path, login_url, data_url, users_path, BASE_DIR
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


async def is_login_successful(response):
    content = await response.text()
    soup = BeautifulSoup(content, 'lxml')
    error = soup.find('span', class_='text-danger', string='Thông tin đăng nhập không đúng!')
    if error:
        logger.error("Đăng nhập thất bại: Thông tin đăng nhập không đúng!")
        return False
    print("Đăng nhập thành công!")
    return True

async def fetch_page(session, url, timeout=20):
    start_time = time.time()
    response = await session.get(url, timeout=timeout)
    print(f"Fetched {url} in {time.time() - start_time:.2f}s")
    return response

async def fetch_page_content(session, url, timeout=20):
    response = await fetch_page(session, url, timeout)
    start_time = time.time()
    content = await response.text()
    print(f"Lấy nội dung trang: {time.time() - start_time:.2f}s")
    return content 

async def login_page(session, login_url, login_id, password):
    page_content = await fetch_page_content(session, login_url)
    start_time = time.time()
    soup = BeautifulSoup(page_content, 'lxml')
    token = soup.find('input', {'name': '__RequestVerificationToken'})
    print(f"Lấy Token xác thực: {time.time() - start_time:.2f}s")
    if not token:
        message = "Không tìm thấy token xác thực!"
        logger.error(message)
        return message
    login_data = {
        "loginID": login_id,
        "password": password,
        "__RequestVerificationToken": token['value']
    }
    start_time = time.time()
    login_response = await session.post(login_url, data=login_data, timeout=20)
    if login_response.status != 200:
        message = f"Đăng nhập không thành công. Mã lỗi: {login_response.status}"
        logger.error(message)
        return message
    print(f"Đã đăng nhập: {time.time() - start_time:.2f}s")
    return None

async def fetch_data(session, login_id, password, user, bot, emails_handler):
    try:
        # Giai đoạn đăng nhập chung cho mỗi phiên
        page = await session.get(login_url)
        html = BeautifulSoup(await page.text(), 'html.parser')
        token = html.find('input', {'name': '__RequestVerificationToken'})['value']
        login_data = {
            "loginID": login_id,
            "password": password,
            "__RequestVerificationToken": token
        }
        await session.post(login_url, data=login_data)

        # Vòng lặp lấy dữ liệu chung
        while True:
            # Lấy emails đồng thời với bảng điểm
            # Lấy emails
            read_page = await session.post(data_url[1], data=login_data)
            html = BeautifulSoup(await read_page.text(), 'html.parser')
            emails_list = html.find('form', id='__formMessageList')
            if not emails_list:
                logger.warning("Không tìm thấy danh sách tin nhắn!")
                await asyncio.sleep(10)
                continue
            # Lấy bảng điểm
            read_page = await session.post(data_url[2], data=login_data)
            html = BeautifulSoup(await read_page.text(), 'html.parser')
            scores_list = html.find('table', class_='table table-bordered table-hover')
            if not scores_list:
                logger.warning("Không tìm thấy bảng điểm!")
                await asyncio.sleep(10)
                continue

            # Cập nhật emails
            links = emails_list.find_all('a', href=True)
            filtered_links = [
                link for link in links if '/Message/Details' in link['href']
            ]
            emails = [
                f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                for link in filtered_links
            ][:1]

            Changed = False
            if emails:
                latest_email = emails[0]
            else:
                latest_email = ""
                
            if "sms" not in user:
                user["sms"] = latest_email
                Changed = True
            else:
                if user["sms"] != latest_email:
                    Changed = True
                    old_message = user["sms"]
                    user["sms"] = latest_email
                    user_id = user['id']
                    user_obj = await bot.fetch_user(int(user_id))
                    if user_obj and old_message != "":
                        await user_obj.send(f"**Tin nhắn mới**:\n{latest_email}")
                        print(f"Tin nhắn mới đã gửi đến {user_id}: {latest_email}")
                    else:
                        print(f"Không tìm thấy người dùng với ID: {user_id}")
                        
            if Changed:
                result = {
                    "id": user["id"],
                    "sms": user.get("sms", "")
                }
                await emails_handler.process_result(result)
                

            # Cập nhật bảng điểm:
            tbody = scores_list.find('tbody')
            trs = tbody.find_all('tr')

            results = []
            for tr in trs:
                tds = tr.find_all('td')
                data = []
                if len(tds) > 2:
                    data = [td.text.strip() for td in tds]
                if data:
                    results.append(data)
                    
            data_results = []
            data_condition = False
            for rs in results:
                if not data_condition:
                    data_condition = True
                    continue
                data_results.append(rs)
            
            # Định dạng dữ liệu
            format_data_json = []
            for data in data_results:
                score_dict = {
                    "LHP": await convert_to_acronym(await remove_accents(data[2])),
                    "Lan hoc": data[4],
                    "QTHT": data[5],
                    "Thi": data[6] if int(data[4]) == 1 else data[8],
                    "Tong": data[7] if int(data[4]) == 1 else data[9]
                }
                format_data_json.append(score_dict)
            # Kiểm tra dữ liệu, cập nhật, thông báo
            scores_file_path = os.path.join(BASE_DIR, 'data', 'scores', f"{login_id}.json")
            old_scores = await load_json(scores_file_path)

            temp = max(len(s["LHP"]) for s in format_data_json)
            length_LHP = max(len("LHP"), temp)
            
            temp = max(len(s["QTHT"]) for s in format_data_json)
            length_QTHT = max(len("QTHT"), temp)

            temp = max(len(s["Thi"]) for s in format_data_json)
            length_DT = max(len("Thi"), temp)

            temp = max(len(s["Tong"]) for s in format_data_json)
            length_TD = max(len("Tong"), temp)
            
            markdown_table = f"|{'LHP': <{length_LHP}}|{'QTHT': <{length_QTHT}}|{'Thi': <{length_DT}}|{'Tong': <{length_TD}}|\n"
            markdown_table += f"|{'-' * length_LHP}|{'-' * length_QTHT}|{'-' * length_DT}|{'-' * length_TD}|\n"
            markdown_table_full = markdown_table

            for item in format_data_json:
                if item["QTHT"] or item["Thi"] or item["Tong"]:
                    markdown_table_full += f"|{item['LHP']:<{length_LHP}}|{item['QTHT']:<{length_QTHT}}|{item['Thi']:<{length_DT}}|{item['Tong']:<{length_TD}}|\n"

            markdown_full_file_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', 'full', f"{login_id}_full.md")

            old_full_markdown = await load_md(markdown_full_file_path)
            if old_full_markdown != markdown_table_full:
                await save_md(markdown_full_file_path, markdown_table_full)
            
            if old_scores != format_data_json:
                if old_scores != []:
                    diffs = []
                    for obj1, obj2 in zip(old_scores, format_data_json):
                        for key in obj1:
                            if obj1[key] != obj2[key]:
                                diff = obj2
                                diffs.append(obj2)
                                break

                    temp = max(len(s["LHP"]) for s in format_data_json)
                    max_length_diffs = max(len(s["LHP"]) for s in diffs)
                    length_LHP = max(temp, max_length_diffs)

                    # Tạo bảng Markdown với độ rộng cột phù hợp
                    for item in diffs:
                        markdown_table += f"|{item['LHP']:<{length_LHP}}|{item['QTHT']:<{length_QTHT}}|{item['Thi']:<{length_DT}}|{item['Tong']:<{length_TD}}|\n"

                    markdown_file_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', f"{login_id}.md")
                    await save_md(markdown_file_path, markdown_table)
                    
                    print(markdown_table)
                    user_id = user['id']
                    user_obj = await bot.fetch_user(int(user_id))
                    if user_obj:
                        message = f"**Cập nhật điểm**:\n```\n{markdown_table}\n```"
                        await user_obj.send(message)
                        print(f"Đã gửi bảng điểm đến {user_id}")
                    else:
                        logger.warning(f"Không tìm thấy người dùng với ID: {user_id}")
                    
                    await save_json(scores_file_path, format_data_json)
                if old_scores == []:
                    await save_json(scores_file_path, format_data_json)
                    
            # Kết thúc vòng 
            await asyncio.sleep(10)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

# From Emails
async def _handle_user_data(login_id, password, user, bot, emails_handler):
    async with aiohttp.ClientSession() as session:
        print(f"Session cho {login_id} đã được tạo và sử dụng.")
        await fetch_data(session, login_id, password, user, bot, emails_handler)

async def handle_users(auth_manager, bot, emails_handler):
    users_data = await load_json(users_path)

    tasks = []
    for user in users_data:
        login_id, encrypted_password = user.get("login_id"), user.get("password")
        start_time = time.time()
        password = await auth_manager.decrypt_password(encrypted_password, user.get("id"), start_time)

        task = asyncio.create_task(_handle_user_data(login_id, password, user, bot, emails_handler))
        tasks.append(task)