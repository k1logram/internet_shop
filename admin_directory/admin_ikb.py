from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Основная админская клавиатура
def main_admin_ikb():
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton('📝 Добавить категорию', callback_data='create_category'), InlineKeyboardButton('📃 Посмотреть категории', callback_data='category_list'))
    ikb.add(InlineKeyboardButton('Просмотр ожидающих заказов', callback_data='view_wait_order'))
    return ikb


# Клавиатура к каждому сообщению для пометки как оплаченный
async def change_status_to_paid(order_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton('Пометить как оплаченный', callback_data=f'change_status_to_paid_{order_id}'), InlineKeyboardButton('Отменить', callback_data=f'admin_confirm_canceled_order_{order_id}'))
    return ikb


# Клавиатура к каждой категории
def change_category_ikb(category_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton('❌ Удалить', callback_data=f'delete_category_{category_id}'), InlineKeyboardButton('📦 Список товаров', callback_data=f'list_product_{category_id}'))
    return ikb


# Клавиатура в начале просмотра всех продуктов в категории
def add_product(category_id):
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton('📸 Добавить товар', callback_data=f'add_product_{category_id}'))
    return ikb


# Клавиатура к каждому товару
def change_product(product_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton('❌ Удалить продукт', callback_data=f'delete_product_{product_id}'), InlineKeyboardButton('📃 Список цен', callback_data=f'price_list_product_{product_id}'))
    return ikb


# Клавиатура в начале просмотра всех количеств в продукте
def add_price_ikb(product_id):
    ikb = InlineKeyboardMarkup(row_width=2)
    ikb.add(InlineKeyboardButton('Добавить цену', callback_data=f'create_price_{product_id}'))
    return ikb


# Клавиатура к каждому количеству
def delete_volume_ikb(volume_id):
    ikb = InlineKeyboardMarkup(row_width=1)
    ikb.add(InlineKeyboardButton('❌ Удалить цену', callback_data=f'delete_volume_{volume_id}'))
    return ikb

