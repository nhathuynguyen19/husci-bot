import asyncio

class Events():
    def __init__(self, 
                       bot):
        self.bot = bot

    async def start(self, auto_notifications, reminder_loop, update_guilds_info):
        print(f'Truy cập bot thành công với tên: {bot.user}')
        await self.bot.tree.sync()
        print("Đã đồng bộ lệnh")
        auto_notifications.start()
        reminder_loop.start()
        update_guilds_info.start()
        print("Ready")