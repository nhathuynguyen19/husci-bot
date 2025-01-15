@bot.event
async def on_ready():
    print(f'Bot đăng nhập thành công với tên: {bot.user}')
    print("Đồng bộ lệnh...")
    await bot.tree.sync()
    print("Đồng bộ lệnh thành công")
    send_notifications.start()
    reminder_loop.start()
    update_guilds_info.start()
    print("Bot sẵn sàng nhận lệnh!")