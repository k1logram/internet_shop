import asyncio
import datetime
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
import other
from create_bot import bot, dp
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from client_directory import client_kb, client_ikb
from data_base import sqlite


admin_id = '6181965444'


class FSMClient(StatesGroup):
    load_contact_number = State()
    load_address = State()
    load_name = State()
    change_the_quantity = State()
    change_quality_by_order = State()
    create_review = State()


@dp.message_handler(content_types=['photo'])
async def get_photo_id(message: types.Message):
    await message.answer(message.photo[-1].file_id)


async def assess_time(time):
    target_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    today = datetime.datetime.today()
    # margin = datetime.timedelta(minutes=1)
    if target_time >= today - datetime.timedelta(minutes=1):
        return 'Сейчас'

    elif target_time.day > int(today.day) - 1:
        return f'Сегодня в {target_time.hour}:{target_time.minute}'

    elif target_time.day > int(today.day) - 2:
        return f'Вчера в {target_time.hour}:{target_time.minute}'

    elif target_time.day > int(today.day) - 3:
        return f'Позавчера в {target_time.hour}:{target_time.minute}'

    else:
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f'{target_time.day} {months[target_time.month - 1]}'


# отправляем каталог
async def func_send_catalog(message):
     await bot.send_message(chat_id=message.from_user.id,
                            text='✨  Каталог продуктов:',
                            reply_markup= await client_ikb.ikb_catalog())


# Обновляем информацию о заказе после любого изменения
async def update_info_about_order(user_id, change_quality=None):
    msg_id = await sqlite.loads_message_object_from_data_base(user_id, 'confirm_order_msg')
    info_by_order = await sqlite.select_info_about_order_by_user_id(user_id, all_info=True)
    order_id = info_by_order[0]
    time_change_order = info_by_order[3]
    status_order = info_by_order[4]
    # Информация о профиле
    info_about_owner_of_order = await sqlite.select_info_about_user_by_user_id(user_id)
    name = info_about_owner_of_order[3]
    contact_number = info_about_owner_of_order[4]
    address = info_about_owner_of_order[5]
    # Определяем время пример - (Сейчас, позавчера, 3 июня)
    time_change_order = await assess_time(time_change_order)
    # Информация о содержимом заказа
    info_by_selected_item_in_order = await order_view_text(user_id, for_confirm_order=True)
    sum_order = info_by_selected_item_in_order[0]
    status_order = await assess_status(status_order)
    # Если в профиле не указана информация, изменяем её
    if contact_number is None or contact_number == '':
        contact_number = '<u>Номер телефона не указан</u>'

    if name is None or name == '':
        name = '<u>Имя получателя не указано</u>'

    if address is None or address == '':
        address = '<u>Адрес доставки не указан</u>'
    # Создаем текст
    result_text = f'''
                               Заказ #{order_id} - {time_change_order}
            {sum_order} р.
    <u>{status_order}</u> ⏱ {time_change_order}

    📞 {contact_number}
    🙋🏻 {name}
    🏡 {address}
    '''
    # Добавляем содержимое
    for item in info_by_selected_item_in_order[1:]:
        result_text += item
    if not change_quality:
        reply_markup = await client_ikb.add_info_in_profile(order_id)
    else:
        reply_markup = await client_ikb.change_quality(order_id, user_id)
    try:
        await bot.edit_message_text(chat_id=user_id,
                                        message_id=msg_id,
                                        text=result_text,
                                        parse_mode='HTML',
                                        reply_markup=reply_markup)
    except: pass


status_name_in_russian = {
    'active': 'Ожидает подтверждения',
    'completed': 'Завершён',
    'in_delivery': 'В доставке',
    'canceled': 'Отменён',
    'verification_by_admin': 'На рассмотрении у магазина',
    'paid': 'Оплачен',

}


# Определяем статус
async def assess_status(status_order):
    return status_name_in_russian.get(status_name_in_russian[status_order], 'не опознанный статус') 


# отправляем сообщение с меняющейся картинкой и кнопкой
# из заранее заготовленного списка
async def func_vitrina(message):
    # отправляем последнее из списка
    product_id = other.Vetrina.photolist[-1]['product_id']
    product_name = await sqlite.select_name_product_by_id(product_id)
    product_price = await sqlite.select_lowest_price_for_product_by_id(product_id)
    message_object = await bot.send_photo(chat_id=message.from_user.id,
                            photo=other.Vetrina.photolist[-1]['photo'],
                            reply_markup=await client_ikb.ikb_random(product_name, product_price))

    send_catalog = False

    for a in range(20):
        if not send_catalog:
            await func_send_catalog(message)
            send_catalog = True

        for item in other.Vetrina.photolist:
            await asyncio.sleep(3)
            product_id = item['product_id']
            product_name = await sqlite.select_name_product_by_id(product_id)
            product_price = await sqlite.select_lowest_price_for_product_by_id(product_id)
            photo = types.InputMediaPhoto(item['photo'])
            try:
                await bot.edit_message_media(message_id=message_object.message_id,
                                            chat_id=message.from_user.id,
                                            media=photo,
                                            reply_markup=await client_ikb.ikb_random(product_name, product_price))
            except: pass


# команда старт
async def func_start_command(message):
    #await bot.send_photo(chat_id=message.from_user.id,
    #                     photo=other.start_message['photo'],
    #                     caption=other.start_message['desc'],
    #                     reply_markup=client_kb.main_kb())
    await func_vitrina(message)
    paid_orders = await sqlite.checking_paid_orders(message.from_user.id)
    if paid_orders:
        await bot.send_message(chat_id=message.from_user.id,
                               text='У вас есть оплаченный заказ, если вы его получили и хотите оставить отзыв, нажмите на кнопку.',
                               reply_markup=await client_ikb.start_get_received_order())


# отправляем прайс-лист
async def func_view_price_list():
    result_str = ''
    categories_list = await sqlite.select_all_id_categories()
    # отправляем товар
    for category_id in categories_list:
        category_name = await sqlite.select_name_category_by_id(category_id)
        result_str = result_str + f'\n{category_name}'
        products_list = await sqlite.select_all_product_for_category(category_id)
        for product_name in products_list:
            result_str = result_str + f'\n    {product_name}'
            product_id = await sqlite.select_id_by_product(product_name)
            values_list = await sqlite.select_all_price_by_product_id(product_id)
            for value in values_list:
                result_str = result_str + f'\n        {value[0]} - {value[1]} р.'

    # возвращаем функцией текст прайс-листа
    return result_str


# функция просмотра всех товаров в категории
async def func_view_chapter(data, callback: types.CallbackQuery):
    category_id = data.split('_')
    category_id = category_id[1]
    category_name = await sqlite.select_name_category_by_id(category_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text=category_name,
                           reply_markup= await client_ikb.ikb_product_in_category(category_id))


# функция просмотра всех цен в товаре
async def func_view_price_for_product(data, callback: types.CallbackQuery):
    product_id = data.split('_')
    product_id = product_id[1]
    product_name = await sqlite.select_name_product_by_id(product_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text=product_name,
                           reply_markup= await client_ikb.ikb_all_price_for_product(product_id))


# Создает текст корзины для пользователя по его user_id
async def order_view_text(user_id, for_confirm_order=False, paid_order=False):
    dict_of_selected = await sqlite.select_info_about_order_by_user_id(user_id)
    if paid_order is True:
        dict_of_selected = await sqlite.select_info_about_order_by_user_id(user_id, paid_order=True)

    res_str = ''
    # Находим сумму всей корзины
    sum_order = 0
    for item in dict_of_selected:
        price = await sqlite.select_price_by_volume_id(item)
        price = int(price) * int(dict_of_selected[item])
        print(price, int(dict_of_selected[item]))
        sum_order += price
    res_str += f'🛒  Корзина – {sum_order} р.'
    count = 1
    if for_confirm_order:
        res_lst = [sum_order]
        for item in dict_of_selected:
            price = await sqlite.select_price_by_volume_id(item)
            quantity = dict_of_selected[item]
            product_id = await sqlite.select_product_id_by_volume_id(item)
            product_name = await sqlite.select_name_product_by_id(product_id)
            volume = await sqlite.select_volume_by_volume_id(item)
            if int(quantity) == 1:
                res_lst.append(f'\n\n{count}. {product_name}\n            {volume}\n      {price} р.')
            else:
                res_lst.append(f'\n\n{count}. {product_name}\n            {volume}\n      {price} р. x {quantity} = {int(price) * int(quantity)}')
            count += 1
        return res_lst

    for item in dict_of_selected:
        price = await sqlite.select_price_by_volume_id(item)
        quantity = dict_of_selected[item]
        product_id = await sqlite.select_product_id_by_volume_id(item)
        product_name = await sqlite.select_name_product_by_id(product_id)
        volume = await sqlite.select_volume_by_volume_id(item)
        if int(quantity) == 1:
            res_str += f'\n\n{count}. {product_name}\n            {volume}\n      {price} р.'
        else:
            res_str += f'\n\n{count}. {product_name}\n            {volume}\n      {price} р. x {quantity} = {int(price) * int(quantity)}'
        count += 1
    return res_str


# показываем ифнормацию и кнопки "В корзину" "Назад"
async def func_product_packaging(data, callback: types.CallbackQuery):
    data = data.split('_')
    volume_id = data[1]
    info_list = await sqlite.select_info_by_volume_id(volume_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text=f'<b>{info_list[0]}</b>\n\n{info_list[1]}  —💰 {info_list[2]} р.',
                           reply_markup=await client_ikb.ikb_product_packing(volume_id),
                           parse_mode='HTML')


async def func_select_reviews(data, callback: types.CallbackQuery, item_id=None):
    '''

    :param data: где нужно взять отзывы
    :param callback: ---
    :return: список отзывов
    '''
    lst_reviews = []
    print('item_id -', item_id)
    if not data.startswith('reviews'):
        data = f'reviews_{data}'
    if data.startswith('reviews_all') or data.startswith('all') or 'all' in data:
        reviews = await sqlite.viewing_all_reviews()
        lst_reviews = [i for i in reviews]
    elif data.startswith('reviews_category') or data.startswith('category') or 'category' in data:
        reviews = await sqlite.viewing_reviews_in_chapter(item_id)
        lst_reviews = [i for i in reviews]
    elif data.startswith('reviews_product') or data.startswith('product') or 'product' in data:
        reviews = await sqlite.viewing_reviews_by_product(item_id)
        lst_reviews = [i for i in reviews]
    # возвращает список кортежей (id товара, содержание отзыва, дата, имя пользователя)
    return lst_reviews


# отправляем первый отзыв
async def func_send_review(lst_review, callback_query, type_review, item_id=None):
    '''

    :param lst_review: список отзывов
    :param callback_query: калбек
    :param type_review: all, category, product
    :return: обьект сообщения отзывов
    '''
    all_count = len(lst_review)
    current_count = str(all_count)[:]
    current_count = int(current_count) - 1
    name_user = lst_review[current_count][4]
    data_reviews = lst_review[current_count][3]
    name_product = lst_review[current_count][1]
    name_product = await sqlite.select_info_by_volume_id(name_product)
    text_reviews = lst_review[current_count][2]
    message_object = await bot.send_message(chat_id=callback_query.from_user.id,
                                            text=f'📜 <b>{name_user}</b>: Отзыв о продукте  ·  {data_reviews}\n{text_reviews}\n\n{name_product[0]} {name_product[1]} {name_product[2]}',
                                            reply_markup=await client_ikb.ikb_change_reviews(all_count, current_count + 1, name_product[0], type_review, item_id=item_id),
                                            parse_mode='HTML')
    return message_object


@dp.message_handler(Text(equals='Вопросы'))
async def send_ask(message: types.Message):
    await message.answer('''
    1. Каким образом работает электросамокат?
   - Электросамокат работает на электрической энергии, которая поступает от аккумулятора и подает электричество на мотор, приводящий в движение заднее колесо.

2. Как долго можно ездить на электросамокате на одном заряде?
   - Дальность поездки на электросамокате зависит от многих факторов, включая мощность аккумулятора, вес пользователя, скорость и условия дороги. В среднем, можно ожидать примерно 15-30 километров на одном заряде.

3. Как быстро развивается скорость на электросамокате?
   - Максимальная скорость на электросамокате зависит от его спецификаций и мощности мотора. Обычно, скорость может достигать от 20 до 50 километров в час.

4. Как долго занимает время зарядки электросамоката?
   - Время зарядки электросамоката зависит от его батареи и зарядного устройства. Обычно, полная зарядка занимает от 2 до 8 часов.

5. Каковы основные преимущества использования электросамоката?
   - Основные преимущества использования электросамоката включают экологичность (не выделяет выбросы вредных веществ), экономию денег на топливе, легкость и удобство в управлении, молниеносную парковку и возможность передвигаться в городской среде на дальние расстояния без физической нагрузки.
    ''')


# команда start и кнопка Каталог
@dp.message_handler(commands='start')
@dp.message_handler(Text(equals='Каталог'))
async def cmd_start(message: types.Message):
    # составляем username по msg.username
    user_name = message.from_user.username
    # при неудаче сохраняем id
    if user_name is None:
        user_name = message.from_user.id

    # записываем пользователя в БД
    await sqlite.add_user_in_data_base(message.from_user.id, user_name)
    price_list_str = await func_view_price_list()
    if price_list_str:
        await message.answer(text=price_list_str)

    await func_start_command(message)


# Отмена ввода данных
@dp.callback_query_handler(text="cancel_load", state='*')
async def cb_cancel_load(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()


# отправляем прайс-лист
@dp.callback_query_handler(text="price-list")
async def cb_send_random_value(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id,
                     text=await func_view_price_list(),
                           parse_mode='HTML')


# отправляем все товары внутри категории
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('category_'))
async def cb_chapter(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await func_view_chapter(callback_query.data, callback_query)


# отправляем все цены о товаре
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('product_'))
async def cb_all_price(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await func_view_price_for_product(callback_query.data, callback_query)


# начало занесения товара в корзину
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('pick'))
async def cb_product_packaging(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await func_product_packaging(callback_query.data, callback_query)


# отправляет все отзывы
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'reviews_all')
async def cb_send_review(callback_query: types.CallbackQuery):
    lst_review = await func_select_reviews(callback_query.data, callback_query)
    await callback_query.message.delete()
    message_reviews_object = await func_send_review(lst_review, callback_query, 'all')
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, message_reviews_object.message_id, 'review')


# отправляет все отзывы о товарах в одной категории
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('reviews_category'))
async def cb_send_review(callback_query: types.CallbackQuery):
    lst_review = await func_select_reviews(callback_query.data, callback_query, item_id=callback_query.data.split('_')[-1])
    await callback_query.message.delete()
    message_reviews_object = await func_send_review(lst_review, callback_query, 'category', item_id=callback_query.data.split('_')[-1])
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, message_reviews_object.message_id, 'review')


# отправляет отзывы о продукте
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('reviews_product'))
async def cb_send_review(callback_query: types.CallbackQuery):
    lst_review = await func_select_reviews(callback_query.data, callback_query, item_id=callback_query.data.split('_')[-1])
    await callback_query.message.delete()
    message_reviews_object = await func_send_review(lst_review, callback_query, 'product', item_id=callback_query.data.split('_')[-1])
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, message_reviews_object.message_id, 'review')


# хендлер калбеков изменения отзывов
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('reviews_change'), state='*')
async def cb_change_review(callback_query: types.CallbackQuery, state: FSMContext):
    try: await state.finish()
    except: pass
    # если пользователь нажимает на номер отзыва на котором он уже находится
    if callback_query.data == 'reviews_change_current':
        await callback_query.answer('Вы и так здесь')
    else:
        item_id = callback_query.data.split('_')[-3]
        if not item_id.isdigit():
            item_id = None

        type_review = callback_query.data.split('_')[-1]
        message_id = callback_query.message.message_id
        lst_review = await func_select_reviews(callback_query.data, callback_query, item_id)
        # количество всех отзывов в пределах которых происходит управление
        all_count = len(lst_review)
        # номер текущего отзыва
        count = callback_query.data.split('_')
        count = count[-2]
        count = int(count) - 1
        name_user = lst_review[count][4]
        data_reviews = lst_review[count][3]
        name_product = lst_review[count][1]
        name_product = await sqlite.select_info_by_volume_id(name_product)
        text_reviews = lst_review[count][2]
        # изменяем обьект сообщения отзывов
        try:
            await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                        text=f'📜 <b>{name_user}</b>: Отзыв о продукте  ·  {data_reviews}\n{text_reviews}\n\n{name_product[0]} {name_product[1]} {name_product[2]}',
                                        message_id=message_id,
                                        reply_markup=await client_ikb.ikb_change_reviews(all_count, count + 1, name_product[0], type_review, item_id=item_id),
                                        parse_mode='HTML')
        except: pass


# Возвращение от изменения количества
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('back_to_confirm_order'), state='*')
async def back_to_confirm_order(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    msg = await sqlite.loads_message_object_from_data_base(callback_query.from_user.id, 'cancel_change')
    try: await bot.delete_message(chat_id=callback_query.from_user.id,
                            message_id=msg)
    except: pass
    order_id = callback_query.data.split('_')[4]
    await callback_query.message.edit_reply_markup(reply_markup=await client_ikb.add_info_in_profile(order_id))


# возвращаемся из товаров в категории в каталог
@dp.callback_query_handler(text="back to catalog")
async def cb_back_to_catalog(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await func_send_catalog(callback_query)


# Начало добавления номера телефона
@dp.callback_query_handler(Text(equals='load_contact_number'), state='*')
async def cmd_start_load_contact_number(callback_query: types.CallbackQuery):
    load_contact_number_msg = await bot.send_message(text='❓ Введите номер телефона получателя (пример: +79248437263)',
                           chat_id=callback_query.from_user.id,
                           reply_markup= await client_ikb.ikb_cancel())
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, load_contact_number_msg.message_id, 'load_contact_number')
    await FSMClient.load_contact_number.set()


# Ввод и сохранение номера телефона
@dp.message_handler(state=FSMClient.load_contact_number)
async def cmd_load_contact_number(message: types.Message, state: FSMContext):
    if message.text.isalpha():
        await message.answer('Введите настоящий номер телефона')
        return

    await sqlite.update_contact_number_for_user(message.from_user.id, message.text)
    load_contact_number_msg = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'load_contact_number')
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=load_contact_number_msg)
    await update_info_about_order(message.from_user.id)
    await message.delete()
    await state.finish()


# Начало добавления имени
@dp.callback_query_handler(Text(equals='load_name'), state='*')
async def cmd_start_load_name(callback_query: types.CallbackQuery):
    load_name_msg = await bot.send_message(text='❓ Введите имя получателя заказа',
                                           chat_id=callback_query.from_user.id,
                                           reply_markup=await client_ikb.ikb_cancel())
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, load_name_msg.message_id, 'load_name')
    await FSMClient.load_name.set()


# Ввод и сохранение имени
@dp.message_handler(state=FSMClient.load_name)
async def cmd_load_name(message: types.Message, state: FSMContext):
    await sqlite.update_name_for_user(message.from_user.id, message.text)
    load_name_msg = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'load_name')
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=load_name_msg)
    await update_info_about_order(message.from_user.id)
    await message.delete()
    await state.finish()


# Начало добавления адреса
@dp.callback_query_handler(Text(equals='load_address'), state='*')
async def cmd_start_load_address(callback_query: types.CallbackQuery):
    load_address_msg = await bot.send_message(text='❓ Введите адрес доставки',
                           chat_id=callback_query.from_user.id,
                           reply_markup=await client_ikb.ikb_cancel())
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, load_address_msg.message_id, 'load_address')
    await FSMClient.load_address.set()


# Ввод и сохранение адреса
@dp.message_handler(state=FSMClient.load_address)
async def cmd_load_address(message: types.Message, state: FSMContext):
    await sqlite.update_address_for_user(message.from_user.id, message.text)
    load_address_msg = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'load_address')
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=load_address_msg)
    await update_info_about_order(message.from_user.id)
    await message.delete()
    await state.finish()


# Показ текущего заказа
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("add_order"), state='*')
async def cmd_add_order(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    # id записи о продукте который помещаем в корзину
    volume_id = callback_query.data.split('_')[2]
    # id записи о пользователе
    user = await sqlite.select_user_by_userid(callback_query.from_user.id)
    # Добавляем продукт в корзину
    await sqlite.add_order(user, volume_id)
    info = await sqlite.select_info_by_volume_id(volume_id)
    await FSMClient.change_the_quantity.set()
    order_text = await order_view_text(callback_query.from_user.id)
    order_view_msg = await bot.send_message(text=order_text,
                                            chat_id=callback_query.from_user.id)
    leave_one = await bot.send_message(chat_id=callback_query.from_user.id,
                           text=f'''❓ Если вам нужно товара
{info[0]} ({info[1]} - {info[2]}) больше, чем одна штука, введите его нужное количество.''',
                           reply_markup= await client_ikb.leave_one())
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, leave_one.message_id, 'leave_one')
    await sqlite.dumps_message_object_in_data_base(callback_query.from_user.id, order_view_msg.message_id, 'order_view')


# Выход из состояния изменения количества товара в корзине
@dp.callback_query_handler(text="leave_one", state=FSMClient.change_the_quantity)
async def cmd_change_the_quantity_one(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    order_view_msg = await sqlite.loads_message_object_from_data_base(callback_query.from_user.id, 'order_view')
    await bot.edit_message_reply_markup(callback_query.from_user.id,
                                        order_view_msg,
                                        reply_markup=await client_ikb.go_to_confirm_ikb())
    await state.finish()


# Изменение количества товара в корзине и выход из состояния
@dp.message_handler(state=FSMClient.change_the_quantity)
async def cmd_change_the_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Введите число')
        return

    if int(message.text) > 99 or int(message.text) <= 0:
        await message.answer('Введите настоящее количество')
        return

    await message.delete()
    message_leave_one_id = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'leave_one')
    # order_view = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'order_view')
    await bot.delete_message(chat_id=message.from_user.id, message_id=message_leave_one_id)
    order_view_msg = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'order_view')
    # await bot.delete_message(chat_id=message.from_user.id, message_id=order_view)
    user = await sqlite.select_user_by_userid(message.from_user.id)
    await sqlite.change_the_quantity_order(message.text, user)
    order_text = await order_view_text(message.from_user.id)
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=order_view_msg,
                                text=order_text,
                                reply_markup=await client_ikb.go_to_confirm_ikb())
    await state.finish()


@dp.callback_query_handler(Text(equals='add_product'), state='*')
async def cmd_confirm_order(callback: types.CallbackQuery):
    await func_send_catalog(callback)


@dp.callback_query_handler(Text(equals='to_leave_order'), state='*')
@dp.callback_query_handler(Text(equals='confirm_order'), state='*')
async def cmd_confirm_order(callback: types.CallbackQuery):
    try: await callback.message.delete()
    except: pass
    # Информация о заказе
    info_by_order = await sqlite.select_info_about_order_by_user_id(callback.from_user.id, all_info=True)
    order_id = info_by_order[0]
    time_change_order = info_by_order[3]
    status_order = info_by_order[4]
    # Информация о профиле
    info_about_owner_of_order = await sqlite.select_info_about_user_by_user_id(callback.from_user.id)
    name = info_about_owner_of_order[3]
    contact_number = info_about_owner_of_order[4]
    address = info_about_owner_of_order[5]
    # Определяем время пример - (Сейчас, позавчера, 3 июня)
    time_change_order = await assess_time(time_change_order)
    # Информация о содержимом заказа
    info_by_selected_item_in_order = await order_view_text(callback.from_user.id, for_confirm_order=True)
    sum_order = info_by_selected_item_in_order[0]
    status_order = await assess_status(status_order)
    # Если в профиле не указана информация, изменяем её
    if contact_number is None or contact_number == '':
        contact_number = '<u>Номер телефона не указан</u>'

    if name is None or name == '':
        name = '<u>Имя получателя не указано</u>'

    if address is None or address == '':
        address = '<u>Адрес доставки не указан</u>'
    # Создаем текст
    result_text = f'''
                           Заказ #{order_id} - {time_change_order}
        {sum_order} р.
<u>{status_order}</u> ⏱ {time_change_order}

📞 {contact_number}
🙋🏻 {name}
🏡 {address}
'''
    # Добавляем содержимое
    for item in info_by_selected_item_in_order[1:]:
        result_text += item
    # Отправляем
    confirm_order_msg = await bot.send_message(chat_id=callback.from_user.id,
                           text=result_text,
                           parse_mode='HTML',
                           reply_markup=await client_ikb.add_info_in_profile(order_id))
    await sqlite.dumps_message_object_in_data_base(callback.from_user.id, confirm_order_msg.message_id, 'confirm_order_msg')


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('canceled_order'), state='*')
async def canceled_order(callback: types.CallbackQuery):
    await callback.message.delete()
    order_id = callback.data.split('_')[-1]
    await bot.send_message(text='Вы точно хотите отменить заказ?',
                           chat_id=callback.from_user.id,
                           reply_markup=await client_ikb.cancel_order_ikb(order_id))


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('confirm_canceled_order'), state='*')
async def confirm_canceled_order(callback: types.CallbackQuery):
    await callback.message.delete()
    order_id = callback.data.split('_')[-1]
    await sqlite.change_order_status(order_id, 'canceled')
    await callback.answer('🗑 Отменил')
    await func_send_catalog(callback)


@dp.callback_query_handler(Text('add_new_product_in_order'))
async def confirm_canceled_order(callback: types.CallbackQuery):
    await callback.message.delete()
    await func_send_catalog(callback)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('change_quality_by'), state='*')
async def start_change_quality_by_order(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[3]
    await callback.message.edit_reply_markup(reply_markup=await client_ikb.change_quality(order_id, callback.from_user.id))


@dp.callback_query_handler(Text(startswith='change_quality'))
async def change_quality_by_order_for_product(callback: types.CallbackQuery, state: FSMContext):
    await FSMClient.change_quality_by_order.set()
    async with state.proxy() as data:
        data['order_id'] = callback.data.split('_')[2]
        data['idx_product'] = callback.data.split('_')[3]
    cancel_change_msg = await bot.send_message(chat_id=callback.from_user.id,
                           text='Введите новое значение количества товара',
                           reply_markup=await client_ikb.ikb_cancel())
    await sqlite.dumps_message_object_in_data_base(callback.from_user.id, cancel_change_msg.message_id,
                                                   'cancel_change')


#
@dp.message_handler(state=FSMClient.change_quality_by_order)
async def change_quality_by_order(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Введите число')
        return

    if int(message.text) > 99 or int(message.text) <= 0:
        await message.answer('Введите настоящее количество')
        return

    async with state.proxy() as data:
        order_id = data['order_id']
        idx_product = data['idx_product']

    new_volume = message.text
    await sqlite.change_the_quantity_product(order_id, idx_product, new_volume)
    cancel_change_msg = await sqlite.loads_message_object_from_data_base(message.from_user.id, 'cancel_change')
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=cancel_change_msg)
    await state.finish()
    await update_info_about_order(message.from_user.id, change_quality=True)
    await message.delete()


# Кнопка подтвердить заказ
@dp.callback_query_handler(Text(startswith='start_payment'))
async def change_quality_by_order_for_product(callback: types.CallbackQuery):
    user = await sqlite.select_user_by_userid(callback.from_user.id)
    # Проверяем все ли данные указаны
    check_profile = await sqlite.check_info_profile_by_user(user)
    order_id = callback.data.split('_')[2]
    status_order = await sqlite.select_status_order_by_order_id(order_id)
    # Если профиль не заполнен полностью отвечаем пользователю и возвращаем функцию
    if check_profile == 'name':
        await callback.answer(show_alert=True,
                              text='Введите своё имя')

    elif check_profile == 'contact_number':
        await callback.answer(show_alert=True,
                              text='Введите номер телефона')

    elif check_profile == 'address':
        await callback.answer(show_alert=True,
                              text='Введите свой адрес')

    elif status_order == 'verification_by_admin':
        await callback.answer(show_alert=True,
                              text='Заказ уже находится на проверке у администратора')

    elif status_order == 'paid':
        await callback.answer(show_alert=True,
                              text='Заказ уже оплачен')

    elif status_order == 'received':
        await callback.answer(show_alert=True,
                              text='Заказ уже получен')

    elif status_order == 'canceled':
        await callback.answer(show_alert=True,
                              text='Заказ отменён')

    elif check_profile is True:
        # Изменяем статус
        await sqlite.change_order_status(order_id, 'verification_by_admin')
        await callback.message.edit_text(text=callback.message.text.replace('Ожидает подтверждения', 'На рассмотрении у магазина'))
        await callback.message.answer(text='Ваш заказ отправлен на расмотрение.')
        info_by_order = callback.message.text.replace('Ожидает подтверждения', 'На рассмотрении у магазина')
        username = callback.from_user.username
        if username is None:
            username = callback.from_user.first_name

        msg_text = f'Заказ от пользователя {username} пришел на проверку.\n\n'
        msg_text += info_by_order
        await bot.send_message(chat_id=admin_id,
                               text=msg_text)


# Кнопка отметить заказ как полученный
@dp.callback_query_handler(Text(equals='start_get_received_order'))
async def change_quality_by_order_for_product(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id,
                           text='Проверьте, этот ли заказ вы получили?')
    msg_text = await order_view_text(callback.from_user.id, paid_order=True)
    await bot.send_message(chat_id=callback.from_user.id,
                           text=msg_text,
                           reply_markup=await client_ikb.get_received_order())


# Помечаем заказ
@dp.callback_query_handler(Text(equals='get_received_order'))
async def change_quality_by_order_for_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await FSMClient.create_review.set()
    try: order_id = await sqlite.select_paid_order_for_user_id(callback.from_user.id)
    except: return
    await sqlite.change_order_status(order_id, 'received')
    await bot.send_message(text='Отлично! Теперь вы можете оставить отзыв.',
                           chat_id=callback.from_user.id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text='Напишите свой отзыв о отправьте его.',
                           reply_markup=await client_ikb.ikb_cancel())
    await bot.send_message(chat_id=admin_id,
                           text=f'Пользователь {callback.from_user.username} отметил заказ номер {order_id} как полученный')
    async with state.proxy() as data:
        data['order_id'] = order_id


# Принимаем текст и создаем отзыв
@dp.message_handler(state=FSMClient.create_review)
async def change_quality_by_order(message: types.Message, state: FSMContext):
    if message.text == 'Каталог' or message.text == 'Вопросы':
        return
    async with state.proxy() as data:
        order_id = data['order_id']
    await sqlite.create_review(order_id, message.text, message.from_user.id)
    await message.answer('Отзыв успешно создан. Спасибо что выбрали наш магазин!')
    await state.finish()
    await func_start_command(message)


def register_client_handler(dp: Dispatcher):
    dp.register_message_handler(cmd_start, state='*')













































