from admin_directory import admin
from create_bot import dp
from aiogram import executor
from data_base import sqlite
from client_directory import client


async def on_startup(_):
    print('Бот вышел в онлайн')
    await sqlite.db_start()



client.register_client_handler(dp)
admin.register_admin_handler(dp)




if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True,
                           on_startup=on_startup)


















