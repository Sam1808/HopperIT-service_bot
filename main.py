import argparse
import logging
import json
import os
import requests
import telegram

from google.cloud import dialogflow
from dotenv import load_dotenv
from functools import partial
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

custom_keyboard = [['Кнопка 1', 'Кнопка 2'], ['Кнопка 3']]
reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)


def get_metcast(location):
    weather_url = f'https://wttr.in/{location}_2p_lang=ru.png'

    response = requests.get(weather_url)
    with open('weather.png', 'wb') as file:
        file.write(response.content)

def send_chat_message(
        update,
        _,
        project_id: str,
        language: str,
        hopper_users: list,
):
    session_id = f"tg-{update.message.from_user['id']}"
    first_name = update.message.from_user['first_name']
    last_name = update.message.from_user['last_name']

    if not update.message.from_user['username'].lower() in hopper_users:
        text = f'''
        {first_name} {last_name}, я завидую твоему упорству. :)
        Давай поболтаем через часок, может меня обновят...
        '''
        update.message.reply_text(text)
        return None

    if 'погода ' in update.message.text.lower():
        location = update.message.text.lower().split(' ')[1]
        if location:
            get_metcast(update.message.text.lower().split(' ')[1])
            update.message.reply_photo(open('weather.png', "rb"))
    else:
        reply = fetch_answer_from_intent(
            project_id, session_id, update.message.text, language
        )

        update.message.reply_text(reply)


def fetch_answer_from_intent(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    logging.info("Session path: {}\n".format(session))

    text_input = dialogflow.TextInput(
            text=text, language_code=language_code
        )
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
    logging.info("=" * 20)
    logging.info(
            "Input: {}".format(response.query_result.query_text)
        )
    logging.info(
            "Output: {}".format(response.query_result.fulfillment_text)
        )
    return response.query_result.fulfillment_text


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


if __name__ == '__main__':

    load_dotenv()
    telegram_token = os.environ['TELEGRAM-TOKEN']
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    language = os.environ['LANGUAGE']
    hopper_users = json.loads(os.environ['HOPPER-USERS'])

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    partial_start = partial(
        start,
        hopper_users=hopper_users
    )

    start_handler = CommandHandler('start', partial_start)
    dispatcher.add_handler(start_handler)

    partial_send_chat_message = partial(
        send_chat_message,
        project_id=dialogflow_project_id,
        language=language,
        hopper_users=hopper_users
    )

    send_chat_message_handler = MessageHandler(
        Filters.text & (~Filters.command),
        partial_send_chat_message
    )
    dispatcher.add_handler(send_chat_message_handler)

    updater.start_polling()
    updater.idle()
