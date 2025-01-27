from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def counter_button(count):
    res = ''
    for i in range(count):
        res = res + "add(KeyboardButton('Кнопка'))"
    return res



def main_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Каталог')).insert(KeyboardButton('Вопросы'))
    return kb

def kb_edit_record() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Изменить')).insert(KeyboardButton('Удалить')).add(KeyboardButton('Отмена'))
    return kb

def kb_cancel() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Отмена'))
    return kb

def kb_pick_payment_method() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Сейчас по карте сбербанк')).insert(KeyboardButton('При получении')).add(KeyboardButton('Отмена'))
    return kb

def ikb_payment() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup
    ikb.add(KeyboardButton('Оплатить')).add(KeyboardButton('Отмена'))
    return ikb


def kb_pick_village() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Калтук').insert('Другая').add('Отмена')
    return kb