from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters import Text, state
from data_base import sqlite
from create_bot import dp, bot
from admin_directory import admin_ikb
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class FSMAdmin(StatesGroup):
    load_category = State()
    load_product = State()
    load_volume = State()
    load_price = State()


def cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Отмена ❌',)
    return kb


# Отмена любого состояния
@dp.message_handler(Text(equals='Отмена ❌'), state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    await message.answer("Отменил",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.finish()
    await cmd_start_admin(message)


# начало админки
@dp.message_handler(commands="admin_mode_s45s41")
async def cmd_start_admin(message: types.Message):
    await bot.send_message(text="✏️ Управление ассортиментов",
                           chat_id=message.from_user.id,
                           reply_markup=admin_ikb.main_admin_ikb())


# Просмотр заказов находящихся на проверке
@dp.callback_query_handler(text="view_wait_order")
async def cmd_add_chapter(callback: types.CallbackQuery):
    order_list = await sqlite.select_wait_order()
    msg_text = ''
    for order_id in order_list:
        owner_order = await sqlite.select_user_name_by_order_id(order_id)
        await bot.send_message(text=f'ID заказа - #{order_id}\n\nВладелец - {owner_order}',
                               reply_markup=await admin_ikb.change_status_to_paid(order_id),
                               chat_id=callback.from_user.id)


# Изменение статуса
@dp.callback_query_handler(Text(startswith='change_status_to_paid'))
async def change_status_to_paid(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[4]
    await callback.message.delete()
    await sqlite.change_order_status(order_id, 'paid')
    await callback.answer('Пометил!')
    client_name = await sqlite.select_user_name_by_order_id(order_id)
    client_id = await sqlite.select_user_id_by_username(client_name)
    await bot.send_message(chat_id=client_id,
                           text='Ваш заказ помечен как оплаченный.')


# начало добавление категории
@dp.callback_query_handler(text="create_category")
async def cmd_add_chapter(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id, '🔤 Введи название категории',
                           reply_markup=cancel_kb())
    await FSMAdmin.load_category.set()


# конец добавление категории
@dp.message_handler(state=FSMAdmin.load_category)
async def cmd_load_category(message: types.Message, state: FSMContext):
    await sqlite.create_category(message.text)
    await message.answer('Ты успешно добавили категорию в базу данных.\nВ управлении можно управлять товарами внутри неё.')
    await state.finish()
    await cmd_start_admin(message)


# список всех категорий
@dp.callback_query_handler(text="category_list")
async def cmd_chapter_list(callback: types.CallbackQuery):
    await bot.send_message(callback.from_user.id, '💼 Вот список всех категорий.\nВы можете удалить ❌, либо добавить товар.')
    list_category_id = await sqlite.select_all_id_categories()
    for category_id in list_category_id:
        name_chapter = await sqlite.select_name_category_by_id(category_id)
        await bot.send_message(callback.from_user.id, text=f'💼 {name_chapter}', reply_markup=admin_ikb.change_category_ikb(category_id))
    await cmd_start_admin(callback)


# Кнопка удалить категорию
@dp.callback_query_handler(Text(startswith="delete_category"))
async def cmd_delete_bot(callback: types.CallbackQuery):
    await callback.answer('Удалил.✅')
    await callback.message.delete()
    category_id = callback.data[16:]
    await sqlite.delete_category_by_id(category_id)


# продукты в категории
@dp.callback_query_handler(Text(startswith="list_product"))
async def cmd_list_product(callback: types.CallbackQuery):
    category_id = callback.data[13:]
    name_category = await sqlite.select_name_category_by_id(category_id)
    list_name_product = await sqlite.select_all_product_for_category(category_id)
    await bot.send_message(callback.from_user.id, f'Вот все товары в категории {name_category}', reply_markup=admin_ikb.add_product(category_id))
    for name_product in list_name_product:
        product_id = await sqlite.select_id_by_product(name_product)
        await bot.send_message(callback.from_user.id,
                               text=name_product,
                               reply_markup=admin_ikb.change_product(product_id))

    await cmd_start_admin(callback)


# начало создания товара
@dp.callback_query_handler(Text(startswith="add_product"))
async def cmd_start_load_product(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data[12:]
    await bot.send_message(callback.from_user.id, "Отправь название товара который ты хочешь добавить", reply_markup=cancel_kb())
    await FSMAdmin.load_product.set()
    async with state.proxy() as data:
        data['category_id'] = category_id


# сохранение товара
@dp.message_handler(state=FSMAdmin.load_product)
async def cmd_load_product(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await sqlite.load_product(message.text, data['category_id'])

    await state.finish()
    await message.answer('Сохранил!✅')
    await cmd_start_admin(message)


@dp.callback_query_handler(Text(startswith="delete_product_"))
async def cmd_start_load_photo(callback: types.CallbackQuery):
    await callback.answer('Удалил.✅')
    await callback.message.delete()
    product_id = callback.data[15:]
    await sqlite.delete_product_by_id(product_id)


# Просмотр всех цен продукта
@dp.callback_query_handler(Text(startswith="price_list_product"))
async def cmd_view_price_list(callback: types.CallbackQuery, product_id=None):
    if product_id is None:
        product_id = callback.data[19:]
    product_name = await sqlite.select_name_product_by_id(product_id)
    await bot.send_message(callback.from_user.id, f'Все цены продукта {product_name}',
                           reply_markup=admin_ikb.add_price_ikb(product_id))
    price_list_for_product = await sqlite.select_volume_by_product_id(product_id)
    for info in price_list_for_product:
        await bot.send_message(callback.from_user.id,
                               text=f'{info[1]} - {info[2]}',
                               reply_markup=admin_ikb.delete_volume_ikb(info[0]))

    await cmd_start_admin(callback)


# Удаляем цену по id
@dp.callback_query_handler(Text(startswith="delete_volume"))
async def cmd_delete_bot(callback: types.CallbackQuery):
    await callback.answer('Удалил.✅')
    await callback.message.delete()
    volume_id = callback.data[14:]
    await sqlite.delete_volume_by_id(volume_id)


# начало добавление цены
@dp.callback_query_handler(Text(startswith="create_price_"))
async def cmd_start_load_price(callback: types.CallbackQuery, state: FSMContext):
    product_id = callback.data[13:]
    await bot.send_message(callback.from_user.id, "Отправь количество. Пример - '10 грамм'",
                           reply_markup=cancel_kb())
    await FSMAdmin.load_volume.set()
    async with state.proxy() as data:
        data['product_id'] = product_id


# Ввод количества
@dp.message_handler(state=FSMAdmin.load_volume)
async def cmd_load_volume(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['volume'] = message.text
    await message.answer('Теперь отправь цену. Пример - "200"')
    await FSMAdmin.next()


# сохранение товара
@dp.message_handler(state=FSMAdmin.load_price)
async def cmd_load_product(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        product_id = data['product_id']
        category_id = await sqlite.select_category_id_by_product_id(product_id)
        await sqlite.load_volume(category_id, product_id, data['volume'], message.text.replace(' ', ''))
    await state.finish()
    await message.answer('Сохранил!✅')
    await cmd_view_price_list(message, product_id=product_id)


# Отмена заказа админом
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('admin_confirm_canceled_order'), state='*')
async def confirm_canceled_order(callback: types.CallbackQuery):
    await callback.message.delete()
    order_id = callback.data.split('_')[-1]
    await sqlite.change_order_status(order_id, 'canceled')
    await callback.answer('🗑 Отменил')
    order_owner_id = await sqlite.select_owner_id_by_order_id(order_id)
    await bot.send_message(chat_id=order_owner_id,
                           text=f'Ваш заказ номер {order_id} был отменён.')


def register_admin_handler(dp: Dispatcher):
    dp.register_message_handler(cmd_cancel, Text(equals='Отмена ❌'), state='*')
    dp.register_message_handler(cmd_start_admin)


