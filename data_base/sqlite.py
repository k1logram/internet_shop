import datetime
import sqlite3 as sq


async def db_start():
    global db, cur

    db = sq.connect('data_base/catalog.db')
    cur = db.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS categories(category_id INTEGER PRIMARY KEY AUTOINCREMENT, name_сategory TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS products(product_id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, name_product TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS volumes(volume_id INTEGER PRIMARY KEY, category_id INTEGER, product_id INTEGER, volume TEXT, price TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS reviews(review_id INTEGER PRIMARY KEY, volume_id INTEGER, content TEXT, data TEXT, name TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS message_object(user_id TEXT, message_object TEXT, type_message TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT, user_name TEXT, name TEXT, contact_number TEXT, address TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS orders(order_id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, list_of_selected TEXT, changed_time TEXT, status TEXT)")
    db.commit()


async def select_lowest_price_for_product_by_id(product_id):
    price = [price for price in cur.execute(f"SELECT price FROM volumes WHERE product_id = '{product_id}'")]
    return min(price[0])


# Берем user id  телеграмме по ID записи в таблице
async def select_user_id_by_user(user):
    user_id = [user_id[0] for user_id in cur.execute(f"SELECT user_id FROM users WHERE id = '{user}'")]
    return user_id[0]


# Берем статус заказа по его id
async def select_status_order_by_order_id(order_id):
    status_order = [status[0] for status in cur.execute(f"SELECT status FROM orders WHERE order_id = '{order_id}'")]
    return status_order[0]


# Берем id первого оплаченного заказа по user_id
async def select_paid_order_for_user_id(user_id):
    user = await select_user_by_userid(user_id)
    order_id = [order[0] for order in cur.execute(f"SELECT order_id FROM orders WHERE user = '{user}' AND status = 'paid'")]
    return order_id[0]


# Проверка есть ли у пользователя оплаченных заказов
async def checking_paid_orders(user_id):
    user = await select_user_by_userid(user_id)
    paid_order = [order[0] for order in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = '{user}' AND status = 'paid'")]
    if len(paid_order) != 0:
        return True
    else:
        return False


# Изменение состояния корзины вместе с временем
async def change_order_status(order_id, new_status):
    time_now = datetime.datetime.now()
    cur.execute(f"UPDATE orders SET (changed_time, status) = ('{time_now}', '{new_status}') WHERE order_id = '{order_id}'")
    db.commit()


# Добавление товара в корзину, с изменением времени
async def add_order(user, volume_id):
    list_of_selected = [i[0] for i in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = '{user}' AND status = 'active'")]
    time_now = datetime.datetime.now()
    if list_of_selected:
        list_of_selected = list_of_selected[0]
        list_of_selected += f' {volume_id}-1'
        print(list_of_selected, user)

        cur.execute(f"UPDATE orders SET (list_of_selected, changed_time) = ('{list_of_selected}', '{time_now}') WHERE user = '{user}' AND status = 'active'")
    else:
        cur.execute("INSERT INTO orders(user, list_of_selected, changed_time, status) VALUES (?, ?, ?, ?)", (user, f'{volume_id}-1', time_now, 'active'))
    db.commit()


# Находим ифнормацию о пользователе по его user_id
async def select_info_about_user_by_user_id(user_id):
    info_by_user = [i for i in cur.execute(f"SELECT * FROM users WHERE user_id = '{user_id}'")]
    return info_by_user[0]


# Изменяем количество последнего выбранного продукта
async def change_the_quantity_order(text, user):
    list_of_selected = [i[0] for i in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = '{user}' AND status = 'active'")]
    list_of_selected = list(list_of_selected[0])
    list_of_selected[-1] = text
    list_of_selected = ''.join(list_of_selected)
    cur.execute(f"UPDATE orders SET list_of_selected = '{list_of_selected}' WHERE user = '{user}' AND status = 'active'")
    db.commit()


# Берем информацию о корзине по user_id
async def select_info_about_order_by_user_id(user_id, all_info=False, paid_order=False):
    user = await select_user_by_userid(user_id)
    if all_info:
        info_by_order = [i for i in cur.execute(f"SELECT * FROM orders WHERE user = '{user}' AND status = 'active'")]
        return info_by_order[0]

    if paid_order is False:
        list_of_selected = [i[0] for i in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = '{user}' AND status = 'active'")]
    elif paid_order is True:
        list_of_selected = [i[0] for i in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = '{user}' AND status = 'paid'")]

    try: list_of_selected = list_of_selected[0].split(' ')
    except: pass
    dict_of_selected = {}
    for item in list_of_selected:
        item = item.split('-')
        dict_of_selected[f'{item[0]}'] = f'{item[1]}'
    # Возвращаем словарь id товара - количество
    return dict_of_selected


async def change_quantity_in_list_of_selected_by_idx(str_of_selected, idx_product, new_volume):
    # Берем строку заказа
    list_of_selected = str_of_selected[0].split(' ')
    # Дробим эту строку
    target_item = list_of_selected[int(idx_product) - 1]
    target_item = target_item.split('-')
    # кол-во list_of_selected[idx] = new_volume
    target_item[1] = str(new_volume)
    target_item = '-'.join(target_item)
    list_of_selected[int(idx_product) - 1] = target_item
    str_of_selected = ' '.join(list_of_selected)
    return str_of_selected


# Изменяем количество продукта по его id в списке
async def change_the_quantity_product(order_id, idx_product, new_volume):
    user = [i[0] for i in cur.execute(f"SELECT user FROM orders WHERE order_id = '{order_id}'")]
    str_of_selected = [i[0] for i in cur.execute(f"SELECT list_of_selected FROM orders WHERE user = {user[0]} AND status = 'active'")]
    # Изменяем строку
    str_of_selected = await change_quantity_in_list_of_selected_by_idx(str_of_selected, idx_product, new_volume)
    # Записываем
    cur.execute(f"UPDATE orders SET list_of_selected = '{str_of_selected}' WHERE user = '{user[0]}' AND status = 'active'")
    db.commit()


# Берем цену по volume_id
async def select_price_by_volume_id(volume_id):
    print(volume_id)
    price = [i[0] for i in cur.execute(f"SELECT price FROM volumes WHERE volume_id = '{volume_id}'")]
    return price[0]


# добавляем пользователя в базу данных
async def add_user_in_data_base(user_id, user_name):
    # проверяем наличие записи об этом пользователе
    last_record = [i for i in cur.execute(f"SELECT * FROM users WHERE user_id = '{user_id}'")]
    if not last_record:
        cur.execute("INSERT INTO users(user_id, user_name) VALUES (?, ?)", (user_id, user_name))
    db.commit()


# Сохраняем имя пользователя
async def update_name_for_user(user_id, name):
    cur.execute(f"UPDATE users SET name = '{name}' WHERE user_id = '{user_id}'")
    db.commit()


# Сохраняем номер телефона пользователя
async def update_contact_number_for_user(user_id, contact_number):
    cur.execute(f"UPDATE users SET contact_number = '{contact_number}' WHERE user_id = '{user_id}'")
    db.commit()


# Берем количество пример - '10 грамм' по value id
async def select_volume_by_volume_id(volume_id):
    volume = [i[0] for i in cur.execute(f"SELECT volume FROM volumes WHERE volume_id = '{volume_id}'")]
    return volume[0]


# Берем id записи о пользователе в таблице по телеграмм user_id
async def select_user_by_userid(user_id):
    user = [user[0] for user in cur.execute(f"SELECT id FROM users WHERE user_id = '{user_id}'")]
    return user[0]


# Сохраняем адрес пользователя
async def update_address_for_user(user_id, address):
    cur.execute(f"UPDATE users SET address = '{address}' WHERE user_id = '{user_id}'")
    db.commit()


# Берем название категории по её id
async def select_name_category_by_id(id):
    name_category = [name[0] for name in cur.execute(f"SELECT name_category FROM categories WHERE category_id = '{id}'")]
    return name_category[0]


async def count_catalog():
    '''
    :return: словарь id категории : кол-во товаров в категории
    '''
    lst_catalog = {}
    for i in cur.execute("SELECT name_product, category_id FROM products").fetchall():
        category_name = await select_name_category_by_id(i[1])
        lst_catalog[i[0]] = category_name
    all_chapter = list(lst_catalog.values())
    count_product = {}
    for a in all_chapter:
        count = [len(i) for i in lst_catalog.values() if i == a]
        a = await select_category_id_by_category_name(a)
        count_product[a] = [len(count)]
    return count_product


# Сохраняем объект сообщения в базу данных
async def dumps_message_object_in_data_base(user_id, message_object_id, type_message):
    check_record = [check[0] for check in cur.execute(f"SELECT message_object FROM message_object WHERE user_id = '{user_id}' AND type_message = '{type_message}'")]
    if check_record:
        cur.execute(f"UPDATE message_object SET message_object = '{message_object_id}' WHERE user_id = '{user_id}' AND type_message = '{type_message}'")

    else:
        cur.execute("INSERT INTO message_object VALUES (?, ?, ?)",
                    (user_id, message_object_id, type_message))
    db.commit()


# Берем id сообщения по user_id и типу сообщения пример - 'review'
async def loads_message_object_from_data_base(user_id, type_message):
    message_object = [obj[0] for obj in cur.execute(f"SELECT message_object FROM message_object WHERE user_id = '{user_id}' AND type_message = '{type_message}'")]
    return message_object[0]


# Находим список всех товаров в БД
async def select_all_name_product_list():
    name_product_list = [name[0] for name in cur.execute(f"SELECT name_product FROM products")]
    return name_product_list


# Находим список всех категорий
async def select_all_name_product():
    name_list = [name[0] for name in cur.execute(f"SELECT name_category FROM categories")]
    return name_list


# Находим все цены всех продуктов в категории
async def select_all_price(category_id):
    price_list = [name[0] for name in cur.execute(f"SELECT price FROM volumes WHERE category_id = '{category_id}'")]
    return price_list


# Находим список цен по ID продукта
async def select_all_price_by_product_id(product_id):
    price_list = [name for name in cur.execute(f"SELECT volume, price FROM volumes WHERE product_id = '{product_id}'")]
    return price_list


# Берем id категории по id количества
async def select_category_id_by_volume_id(volume_id):
    try: volume_id = volume_id.split(' ')[0]
    except: pass
    category_id = [id[0] for id in cur.execute(f"SELECT category_id FROM volumes WHERE volume_id = '{volume_id}'")]
    return category_id[0]


# Берем id продукта по названию
async def select_product_id_by_name(name_product):
    product_id = [id[0] for id in cur.execute(f"SELECT product_id FROM products WHERE name_product = '{name_product}'")]
    return product_id[0]


# По id количества берем id продукта
async def select_product_id_by_volume_id(volume_id):
    try: volume_id = volume_id.split(' ')[0]
    except: pass
    product_id = [id[0] for id in cur.execute(f"SELECT product_id FROM volumes WHERE volume_id = '{volume_id}'")]
    return product_id[0]


async def select_name_by_user(user):
    name = [name[0] for name in cur.execute(f"SELECT name FROM users WHERE id = '{user}'")]
    return name[0]


async def select_contact_number_by_user(user):
    contact_number = [number[0] for number in cur.execute(f"SELECT contact_number FROM users WHERE id = '{user}'")]
    return contact_number[0]


async def select_address_by_user(user):
    address = [address[0] for address in cur.execute(f"SELECT address FROM users WHERE id = '{user}'")]
    return address[0]


# Проверка данных профиля
async def check_info_profile_by_user(user):
    name = await select_name_by_user(user)
    contact_number = await select_contact_number_by_user(user)
    address = await select_address_by_user(user)
    if name is None:
        return 'name'
    if contact_number is None:
        return 'contact_number'
    if address is None:
        return 'address'
    else:
        return True


# Информация о товаре
async def select_info_by_volume_id(volume_id):
    # Если в функцию передается строка list_of_selected берем первый элемент
    try: volume_id = volume_id.split(' ')[0]
    except: pass
    info_list = []
    for info in cur.execute(f"SELECT product_id, volume, price FROM volumes WHERE volume_id = '{volume_id}'").fetchall():
        name_product = await select_name_product_by_id(info[0])
        info_list.append((name_product, info[1], info[2]))
    # Возвращаем кортеж (Имя продукта, название пример - "10 грамм", цена)
    return info_list[0]


# Берем название категории по её id
async def select_category_id_by_category_name(category_name):
    category_id = [i[0] for i in cur.execute(f"SELECT category_id FROM categories WHERE name_сategory = '{category_name}'")]
    return category_id[0]


async def select_category_name_by_category_id(category_id):
    category_name = [i[0] for i in cur.execute(f"SELECT name_category FROM categories WHERE сategory_id = '{category_id}'")]
    return category_name[0]


# Находим все продукты в категории по ID
async def select_all_product_by_category_id(category_id):
    product_list = [name[0] for name in cur.execute(f"SELECT name_product FROM products WHERE category_id = '{category_id}'")]
    return product_list


# Находим информацию о продукте по его id
async def search_all_price_for_product(product_id):
    info_list = []
    for info in cur.execute(f"SELECT category_id, volume, price, volume_id FROM volumes WHERE product_id = '{product_id}'").fetchall():
        category_name = await select_name_category_by_id(info[0])
        info_list.append((category_name, info[1], info[2], info[3]))

    return info_list


# Считаем количество всех отзывов
async def counter_reviews_all():
    lst = [i for i in cur.execute(f"SELECT volume_id FROM reviews")]
    return len(lst)


# Берем id категории в которой находится нужный нам продукт
async def select_category_id_by_product_id(product_id):
    category_id = [i[0] for i in cur.execute(f"SELECT category_id FROM products WHERE product_id = '{product_id}'")]
    return category_id[0]


# Считаем количество отзывов в категории по её id
async def counter_reviews_in_chapter(category_id_input):
    res = 0
    # Берем все id количеств
    for volume_id in cur.execute(f"SELECT volume_id FROM reviews").fetchall():
        # Берем id категории по id количества
        category_id = await select_category_id_by_volume_id(volume_id[0])
        if int(category_id) == int(category_id_input):
            res += 1

    return res


# Считаем количество отзывов о продукте по его id
async def counter_reviews_by_product_id(product_id_input):
    res = 0
    # Берем все id количеств
    for volume_id in cur.execute(f"SELECT volume_id FROM reviews").fetchall():
        # Берем id категории по id количества
        product_id = await select_product_id_by_volume_id(volume_id[0])
        if int(product_id) == int(product_id_input):
            res += 1
    return res


# Берем id всех продуктов в категории
async def select_all_product_id_by_category_id(category_id):
    res = [i[0] for i in cur.execute(f"SELECT product_id FROM products WHERE category_id = '{category_id}'")]
    return res


# Берем id всех количеств в продукте
async def select_all_rowid_by_product(product_id):
    res = [i[0] for i in cur.execute(f"SELECT volume_id FROM volumes WHERE product_id = '{product_id}'")]
    return res


# Берем матрицу всех отзывов
async def viewing_all_reviews():
    lst = [i for i in cur.execute(f"SELECT * FROM reviews")]
    return lst


# Берем матрицу всех отзывов в категории
async def viewing_reviews_in_chapter(category_id_input):
    res = []
    for review in cur.execute(f"SELECT * FROM reviews").fetchall():
        category_id = await select_category_id_by_volume_id(review[1])
        if int(category_id) == int(category_id_input):
            res.append(review)
    return res


# Берем матрицу отзывов о продукте по его id
async def viewing_reviews_by_product(product_id_input):
    res = []
    for review in cur.execute(f"SELECT * FROM reviews").fetchall():
        product_id = await select_product_id_by_volume_id(review[1])
        if int(product_id) == int(product_id_input):
            res.append(review)
    return res


# Берем строку формата "id количества-объем id количества-объем" у попределенного заказа по его id
async def select_list_of_selected_by_order_id(order_id):
    list_of_selected = [lst[0] for lst in cur.execute(f"SELECT list_of_selected FROM orders WHERE order_id = '{order_id}'")]
    return list_of_selected[0]


# Создаем отзыв о количестве
async def create_review(order_id, content, user_id):
    data = datetime.date.today()
    info_by_user = await select_info_about_user_by_user_id(user_id)
    list_of_selected = await select_list_of_selected_by_order_id(order_id)
    try: list_of_selected = list_of_selected.split(' ')
    except: list_of_selected = [list_of_selected]
    volumes_id_list = ''
    for item in list_of_selected:
        volumes_id_list += f"{item.split('-')[0]} "

    cur.execute("INSERT INTO reviews(volume_id, content, data, name) VALUES (?, ?, ?, ?)", (volumes_id_list, content, data, info_by_user[3]))
    db.commit()


# админская часть
# добавление категории
async def create_category(name_category):
    cur.execute("INSERT INTO categories(name_сategory) VALUES (?)", (name_category,))
    db.commit()


# берет id всех категорий
async def select_all_id_categories():
    id_list = [i[0] for i in cur.execute(f"SELECT category_id FROM categories")]
    return id_list


# берет имя категории по ее id
async def select_name_category_by_id(category_id):
    name_chapter = [i[0] for i in cur.execute(f"SELECT name_сategory FROM categories WHERE category_id = {category_id}")]
    return name_chapter[0]


# берет имя товара по его id
async def select_name_product_by_id(product_id):
    name_chapter = [i[0] for i in cur.execute(f"SELECT name_product FROM products WHERE product_id = '{product_id}'")]
    return name_chapter[0]


# берет все названия товаров в категории
async def select_all_product_for_category(category_id):
    list_product_in_category = [i[0] for i in cur.execute(f"SELECT name_product FROM products WHERE category_id = '{category_id}'")]
    return list_product_in_category


# добавляет новый товар
async def load_product(name_product, category_id):
    cur.execute("INSERT INTO products(category_id, name_product) VALUES (?, ?)", (category_id, name_product))
    db.commit()


# Берем ID продукта по названию
async def select_id_by_product(name_product):
    name_chapter = [i[0] for i in cur.execute(f"SELECT product_id FROM products WHERE name_product = '{name_product}'")]
    return name_chapter[0]


# Удаляем количество с ценой
async def delete_volume_by_id(volume_id):
    cur.execute(f"DELETE FROM volumes WHERE volume_id = '{volume_id}'")
    db.commit()


# Удаляем продукт по id
async def delete_product_by_id(product_id):
    cur.execute(f"DELETE FROM volumes WHERE product_id = '{product_id}'")
    cur.execute(f"DELETE FROM products WHERE product_id = '{product_id}'")
    db.commit()


# Удаляем категорию
async def delete_category_by_id(category_id):
    cur.execute(f"DELETE FROM categories WHERE category_id = '{category_id}'")
    cur.execute(f"DELETE FROM products WHERE category_id = '{category_id}'")
    cur.execute(f"DELETE FROM volumes WHERE category_id = '{category_id}'")
    db.commit()


# Берем категорию продукта
async def select_chapter_by_product_name(product_name):
    category_id = [i[0] for i in cur.execute(f"SELECT category_id FROM products WHERE name_product = '{product_name}'")]
    name_category = await select_name_category_by_id(category_id[0])
    return name_category


# Создаем ценник
async def load_volume(category_id, product_id, volume, price):
    cur.execute("INSERT INTO volumes(category_id, product_id, volume, price) VALUES (?, ?, ?, ?)", (category_id, product_id, volume, price))
    db.commit()


#  Берет (количество цена) о продукте по его id
async def select_volume_by_product_id(product_id):
    volume_list = [volume for volume in cur.execute(f"SELECT volume_id, volume, price FROM volumes WHERE product_id = '{product_id}'")]
    return volume_list


# Просмотр ожидающих проверки магазином заказов
async def select_wait_order():
    order_list = [order[0] for order in cur.execute(f"SELECT order_id FROM orders WHERE status = 'verification_by_admin'")]
    return order_list


# Берем username владельца заказа по его id
async def select_user_name_by_order_id(order_id):
    user = [user[0] for user in cur.execute(f"SELECT user FROM orders WHERE order_id = '{order_id}'")]
    username = [username[0] for username in cur.execute(f"SELECT user_name FROM users WHERE id = '{user[0]}'")]
    return username[0]


async def select_user_id_by_username(username):
    if username.isdigit():
        return username
    user_id = [user_id[0] for user_id in cur.execute(f"SELECT user_id FROM users WHERE user_name = '{username}'")]
    return user_id[0]


# Берем id создателя заказа по order id
async def select_owner_id_by_order_id(order_id):
    user = [user[0] for user in cur.execute(f"SELECT user FROM orders WHERE order_id = '{order_id}'")]
    user_id = await select_user_id_by_user(user[0])
    return user_id


