from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data_base import sqlite


async def ikb_random(name, price) -> InlineKeyboardMarkup:
    product_id = await sqlite.select_product_id_by_name(name)
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton(text=f'{name}, от {price}.', callback_data=f'product_{product_id}'))
    return ikb


async def ikb_cancel() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton(text='✖️ отмена', callback_data=f'cancel_load'))
    return ikb


# Клавиатура при получении заказа
async def start_get_received_order():
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton(text='Отметить заказ как полученный', callback_data='start_get_received_order'))
    return ikb


async def get_received_order():
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton(text='Все верно', callback_data='get_received_order'))
    return ikb


async def go_to_confirm_ikb():
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton(text='К оформлению', callback_data='confirm_order'), InlineKeyboardButton('➕ Добавить товар', callback_data='add_new_product_in_order'))
    return ikb


async def ikb_catalog() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(row_width=2)
    counter_catalog = await sqlite.count_catalog()
    count_reviews = await sqlite.counter_reviews_all()
    for i in counter_catalog:
        category_name = await sqlite.select_name_category_by_id(i)
        ikb.add(InlineKeyboardButton(text=f'{category_name} | {counter_catalog[i][0]}', callback_data=f'category_{i}'))
    ikb.add(InlineKeyboardButton(text='💲 Прайс-Лист', callback_data='price-list'))
    if count_reviews > 0:
        ikb.insert(InlineKeyboardButton(text=f'📜 Отзывы | {count_reviews}', callback_data='reviews_all'))
    return ikb


async def add_info_in_profile(order_id):
    ikb = InlineKeyboardMarkup(row_width=3)
    ikb.add(InlineKeyboardButton('📞 Телефон', callback_data=f'load_contact_number'), InlineKeyboardButton('👨 Имя', callback_data=f'load_name'), InlineKeyboardButton('🏡 Адрес', callback_data=f'load_address'))
    ikb.add(InlineKeyboardButton('➕ Добавить товар', callback_data='add_new_product_in_order'), InlineKeyboardButton('✏️ Изменить количество', callback_data=f'change_quality_by_{order_id}'))
    ikb.add(InlineKeyboardButton('✅ Подтвердить заказ', callback_data=f'start_payment_{order_id}'), InlineKeyboardButton('🙅‍♂️ Отменить заказ', callback_data=f'canceled_order_{order_id}'))
    return ikb


async def change_quality(order_id, user_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    dict_of_selected = await sqlite.select_info_about_order_by_user_id(user_id)
    for idx, item in enumerate(dict_of_selected):
        idx = str(idx + 1)
        ikb.insert(InlineKeyboardButton(text=f'✏️ {idx}', callback_data=f'change_quality_{order_id}_{idx}'))

    ikb.add(InlineKeyboardButton(text='⬅ назад', callback_data=f'back_to_confirm_order_{order_id}'))
    return ikb


async def cancel_order_ikb(order_id):
    ikb = InlineKeyboardMarkup(row_width=3)
    ikb.add(InlineKeyboardButton('🗑 Отменить', callback_data=f'confirm_canceled_order_{order_id}'), InlineKeyboardButton('📁 Оставить', callback_data='to_leave_order'))
    return ikb


async def ikb_product_in_category(category_id) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(row_width=2)
    list_product = await sqlite.select_all_product_by_category_id(category_id)
    count_reviews_in_chapter = await sqlite.counter_reviews_in_chapter(category_id)
    for name_product in list_product:
        product_id = await sqlite.select_product_id_by_name(name_product)
        ikb.add(InlineKeyboardButton(text=name_product, callback_data=f'product_{product_id}'))

    if count_reviews_in_chapter > 0:
        ikb.add(InlineKeyboardButton(text=f'📜 Отзывы | {count_reviews_in_chapter}', callback_data=f'reviews_category_{category_id}'))

    ikb.add(InlineKeyboardButton(text='💲 Прайс-Лист', callback_data='price-list')).add(InlineKeyboardButton(text='⬅️ Назад в каталог', callback_data='back to catalog'))
    return ikb


async def leave_one():
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton(text='👍 хватит и одного', callback_data='leave_one'))
    return ikb


async def ikb_all_price_for_product(product_id) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(row_width=2)
    list_price = await sqlite.search_all_price_for_product(product_id)
    count_reviews_by_product = await sqlite.counter_reviews_by_product_id(product_id)
    for i in list_price:
        ikb.add(InlineKeyboardButton(text=f'🛒 {i[0]}, {i[1]} - {i[2]} р.', callback_data=f'pick_{i[3]}'))

    category_id = await sqlite.select_category_id_by_product_id(product_id)
    if count_reviews_by_product > 0:
        ikb.add(InlineKeyboardButton(text=f'📜 Отзывы | {count_reviews_by_product}', callback_data=f'reviews_product_{product_id}'))

    ikb.add(InlineKeyboardButton(text='⬅️ Назад в каталог', callback_data=f'category_{category_id}')).add(InlineKeyboardButton(text='💲 Прайс-Лист', callback_data='price-list'))
    return ikb


async def ikb_product_packing(volume_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    info_volume = await sqlite.select_info_by_volume_id(volume_id)
    product_id = await sqlite.select_product_id_by_volume_id(volume_id)
    ikb.add(InlineKeyboardButton(text=f'🛒 В корзину', callback_data=f'add_order_{volume_id}')).insert(InlineKeyboardButton(text='⬅ назад', callback_data=f'product_{product_id}'))
    return ikb


async def ikb_change_reviews(all_count, current_count, product, type_review, item_id=None):
    if item_id is None:
        item_id = ''
    else:
        item_id = f'_{item_id}'

    product_id = await sqlite.select_product_id_by_name(product)
    all_count = int(all_count)
    current_count = int(current_count)
    ikb = InlineKeyboardMarkup(row_width=5)
    product_button = InlineKeyboardButton(text=f'{product}', callback_data=f'product_{product_id}')
    current = InlineKeyboardButton(text=f' ·{current_count}· ', callback_data='reviews_change_current')
    operation_1 = InlineKeyboardButton(text=f'{current_count - 1} ➡️', callback_data=f'reviews_change{item_id}_{current_count - 1}_{type_review}')
    operation_0 = InlineKeyboardButton(text='1 ➡️', callback_data=f'reviews_change{item_id}_1_{type_review}')
    operation_addition_1 = InlineKeyboardButton(text=f'⬅️{current_count + 1}', callback_data=f'reviews_change{item_id}_{current_count + 1}_{type_review}')
    operation_addition_all = InlineKeyboardButton(text=f'⬅️{all_count}', callback_data=f'reviews_change{item_id}_{all_count}_{type_review}')

    if int(all_count) == 2:
        if int(current_count) == 2:
            ikb.add(product_button).add(current).insert(operation_1)

        elif int(current_count) == 1:
            ikb.add(product_button).add(operation_addition_1).insert(current)

    elif all_count == 3:
        if int(current_count) == 3:
            ikb.add(product_button).add(current).insert(operation_1).insert(operation_0)

        elif int(current_count) == 2:
            ikb.add(product_button).add(operation_addition_1).insert(current).insert(operation_1)

        elif current_count == 1:
            ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current)

    elif int(all_count) == 1:
        ikb.add(product_button).add(current)

    elif current_count == 1:
        ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current)

    elif int(all_count) == int(current_count):
        ikb.add(product_button).add(current).insert(operation_1).insert(operation_0)

    elif (int(current_count) + 1) == int(all_count):
        ikb.add(product_button).add(operation_addition_1).insert(current).insert(operation_1).insert(operation_0)

    elif (int(current_count) - 1) == 1:
        ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current).insert(operation_0)

    elif (int(current_count) + 2) != all_count and (int(current_count) - 2) != 1:
        ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current).insert(operation_1).insert(operation_0)

    elif current_count == 1:
        ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current)

    else:
        ikb.add(product_button).add(operation_addition_all).insert(operation_addition_1).insert(current).insert(
            operation_1).insert(operation_0)

    ikb.add(InlineKeyboardButton(text='⬅️ Назад в каталог', callback_data='back to catalog'))

    return ikb








