import argparse
import json
import os
import telegram

from dotenv import load_dotenv
from functools import partial
from telegram.ext import CommandHandler
from telegram.ext import Updater

custom_keyboard = [['Кнопка 1', 'Кнопка 2'], ['Кнопка 3']]
reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)


def start(
        update,
        context,
        hopper_users: list
):
    print(update.message.from_user)  # TODO:отладочный принт
    first_name = update.message.from_user['first_name']
    last_name = update.message.from_user['last_name']
    if update.message.from_user['username'].lower() in hopper_users:
        text = f'''
        Привет {first_name} {last_name}, рад видеть тебя. :)
        Чем могу помочь?
        '''
        update.message.reply_text(text, reply_markup=reply_markup)

    else:
        text = f'''
        Привет {first_name} {last_name}, мы с тобой пока не знакомы :(.
        Давай встретимся позже!
        '''
        update.message.reply_text(text)


def get_telegram_usernames():  # TODO:вывести файл из функции
    hopper_users = []
    with open('QA.json', 'r') as file:
        raw_data = json.load(file)
    for phrase_part in raw_data:
        answer = raw_data[phrase_part]['answer'][0]
        if 'Telegram:' in answer:
            telegram_info = answer.split('Telegram:')[1]
            if telegram_info:
                hopper_users.append(sanitize_telegram_username(telegram_info))
    return hopper_users


def sanitize_telegram_username(raw_username: str):
    if '@' in raw_username:
        username = raw_username.replace('@', '').split(' ')[0]
        return username.lower()
    elif '/' in raw_username:
        username = raw_username.split('/')[-1]
        return username.lower()
    username = raw_username
    return username.lower()


if __name__ == '__main__':

    load_dotenv()
    telegram_token = os.environ['TELEGRAM-TOKEN']

    hopper_users = get_telegram_usernames()

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    partial_start = partial(
        start,
        hopper_users=hopper_users
    )

    start_handler = CommandHandler('start', partial_start)
    dispatcher.add_handler(start_handler)

    updater.start_polling()
    updater.idle()
