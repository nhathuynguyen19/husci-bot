import aiohttp, time, asyncio, os, unicodedata, discord
from bs4 import BeautifulSoup
from config import logger, convert_to_acronym
from modules.utils.file import save_txt, load_json, save_json, remove_accents, save_md, load_md
from paths import login_url, data_url, users_path, BASE_DIR, path_creator
from modules.utils.switch import score_switch
from modules.utils.autopush import push_to_git

processed_users = set()
tasks_phase = []

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
        try:
            page = await session.get(login_url, timeout=20)
        except asyncio.TimeoutError:
            logger.error("Request bị timeout sau 20 giây")
        except Exception as e:
            logger.error(f"Lỗi xảy ra: {e}")
            
        html = BeautifulSoup(await page.text(), 'html.parser')
        token = html.find('input', {'name': '__RequestVerificationToken'})['value']
        login_data = {
            "loginID": login_id,
            "password": password,
            "__RequestVerificationToken": token
        }
        async with session.post(login_url, data=login_data) as response:
            html = BeautifulSoup(await response.text(), 'html.parser')
        user_id_spec = user["id"]
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi: {e}")
        await asyncio.sleep(10)
    print(f"(fetch data) Đã đăng nhập thành công với ID: {login_id}")
        
    # Vòng lặp lấy dữ liệu chung
    while True:
        # Lấy emails đồng thời với bảng điểm
        # Lấy emails
        try:
            try:
                read_page = await session.post(data_url[1], data=login_data, timeout=20)
            except asyncio.TimeoutError:
                logger.error("Request bị timeout sau 20 giây")
            except Exception as e:
                logger.error(f"Lỗi xảy ra: {e}")

            html = BeautifulSoup(await read_page.text(), 'html.parser')
            emails_list = html.find('form', id='__formMessageList')
            if not emails_list:
                logger.warning("Không tìm thấy danh sách tin nhắn!")
                await asyncio.sleep(10)
                continue
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi: {e}")
        print(f"(fetch data) Đã lấy danh sách tin nhắn của {login_id}")
            
        # Lấy bảng điểm
        try:
            read_page = await session.post(data_url[2], data=login_data)
            html = BeautifulSoup(await read_page.text(), 'html.parser')
            scores_list = html.find('table', class_='table table-bordered table-hover')
            if not scores_list:
                logger.warning("Không tìm thấy bảng điểm!")
                await asyncio.sleep(10)
                continue
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi: {e}")
        print(f"(fetch data) Đã lấy bảng điểm của {login_id}")

        # Cập nhật emails
        try:
            links = emails_list.find_all('a', href=True)
            filtered_links = [
                link for link in links if '/Message/Details' in link['href']
            ]
            emails = [
                f"[{link.text.strip()}](https://student.husc.edu.vn{link['href']})"
                for link in filtered_links
            ][:1]

            if emails:
                latest_email = emails[0]
            else:
                latest_email = ""
                        
            await emails_handler.process_result(latest_email, user_id_spec, bot)   
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi: {e}")

        # Cập nhật bảng điểm:
        try:
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
            for rs in results:
                data_results.append(rs)
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi: {e}")
        
        # Định dạng dữ liệu
        try:
            format_data_json = []
            for data in data_results:
                score_dict = {
                    "LopHP": await convert_to_acronym(await remove_accents(data[2])),
                    "Lan hoc": data[4],
                    "QTHT": data[5],
                    "THI": data[6] if int(data[4]) == 1 else data[8],
                    "TONG": data[7] if int(data[4]) == 1 else data[9]
                }
                format_data_json.append(score_dict)
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi: {e}")

        # Kiểm tra dữ liệu, cập nhật, thông báo
        scores_file_path = os.path.join(BASE_DIR, 'data', 'scores', 'info', f"{login_id}.json")
        path_creator(scores_file_path)
        
        old_scores = await load_json(scores_file_path)

        temp = max(len(s["LopHP"]) for s in format_data_json)
        length_LHP = max(len("LopHP"), temp)
        
        temp = max(len(s["QTHT"]) for s in format_data_json)
        length_QTHT = max(len("QTHT"), temp)

        temp = max(len(s["THI"]) for s in format_data_json)
        length_DT = max(len("THI"), temp)

        temp = max(len(s["TONG"]) for s in format_data_json)
        length_TD = max(len("TONG"), temp)
        
        markdown_table = f"|{'LopHP': <{length_LHP}}|{'QTHT': <{length_QTHT}}|{'THI': <{length_DT}}|{'TONG': <{length_TD}}|\n"
        markdown_table += f"|{'-' * length_LHP}|{'-' * length_QTHT}|{'-' * length_DT}|{'-' * length_TD}|\n"
        markdown_table_full = markdown_table

        for item in format_data_json:
            if item["QTHT"] or item["THI"] or item["TONG"]:
                markdown_table_full += f"|{item['LopHP']:<{length_LHP}}|{item['QTHT']:<{length_QTHT}}|{item['THI']:<{length_DT}}|{item['TONG']:<{length_TD}}|\n"

        markdown_full_file_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', 'full', f"{login_id}_full.md")
        path_creator(markdown_full_file_path)

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

                temp = max(len(s["LopHP"]) for s in format_data_json)
                max_length_diffs = max(len(s["LopHP"]) for s in diffs)
                length_LHP = max(temp, max_length_diffs)

                # Tạo bảng Markdown với độ rộng cột phù hợp
                for item in diffs:
                    if item["QTHT"] or item["THI"] or item["TONG"]:
                        markdown_table += f"|{item['LopHP']:<{length_LHP}}|{item['QTHT']:<{length_QTHT}}|{item['THI']:<{length_DT}}|{item['TONG']:<{length_TD}}|\n"

                markdown_file_path = os.path.join(BASE_DIR, 'data', 'scores', 'markdowns', 'last', f"{login_id}.md")
                path_creator(markdown_file_path)
                
                await save_md(markdown_file_path, markdown_table)
                
                user_id = user['id']
                user_obj = await bot.fetch_user(int(user_id))
                if user_obj and score_switch:
                    message = f"**Cập nhật điểm**:\n```\n{markdown_table}\n```"
                    await user_obj.send(message)
                    print(f"Đã gửi bảng điểm đến {user_id}")
                else:
                    logger.warning(f"Không tìm thấy người dùng với ID: {user_id}")
                
                await save_json(scores_file_path, format_data_json)
                await push_to_git(BASE_DIR, "Update scores")
            if old_scores == []:
                await save_json(scores_file_path, format_data_json)
                await push_to_git(BASE_DIR, "Update scores")
                
        # Kết thúc vòng 
        await asyncio.sleep(90)

# From Emails
async def _handle_user_data(login_id, password, user, bot, emails_handler):
    async with aiohttp.ClientSession() as session:
        print(f"Session cho {login_id} đã được tạo và sử dụng.")
        await fetch_data(session, login_id, password, user, bot, emails_handler)

async def handle_users(auth_manager, bot, emails_handler):
    global processed_users
    global tasks_phase
    
    while True:
        users_data = await load_json(users_path)

        current_login_ids = {user.get("login_id") for user in users_data}

        processed_users = processed_users.intersection(current_login_ids)

        for user in users_data:
            login_id = user.get("login_id")
            if login_id in processed_users:
                continue 

            try:
                encrypted_password = user.get("password")
                start_time = time.time()
                password = await auth_manager.decrypt_password(encrypted_password, user.get("id"), start_time)

                task = asyncio.create_task(_handle_user_data(login_id, password, user, bot, emails_handler))
                tasks_phase.append(task)
            except Exception as e:
                print(f"Đã xảy ra lỗi: {e}")
                
            processed_users.add(login_id)

        await asyncio.sleep(5)