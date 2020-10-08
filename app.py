#!/usr/bin/python
# -*- coding: utf-8 -*-
# Модуль для работы с потоками
from threading import Thread
# Модуль для выполнения запросов к Telegram API
import requests
 # Модуль для синтаксического анализа ответов от Telegram API
import json
# Модуль работы с временем
import time
# Модуль работы с ссылками
import urllib
# Модуль БД
from db import DB

# Модуль обработки новостей
import feed

##  Глобальные переменные
# Определяем токен нашего бота, который нам необходим для аутентификации с помощью Telegram API.
TOKEN = "git"
# Базовый URL-адрес, который будем использовать во всех наших запросах к API.
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


# Проинициализируем локальную базу данных
db = DB()


# Функция просто загружает контент по URL и возвращает стоку. 
# Дополнительно, мы ее дектодируем в формат utf8.
def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

# Функция получает строковый ответ. Telegram отдает ответ в формате JSON.
# после чего, сериализуем строку в словарь.
def get_json_from_url(url):
    content = get_url(url)
    json_data = json.loads(content)
    return json_data


# Функция запрашивает список обновлений(сообщений отправленных нашему боту)
def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    json_data = get_json_from_url(url)
    return json_data

# Функция перебирает все идентификаторы сообщений и находит максимальный.
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


# Функция для отправки эхо-сообщений
def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            user_id = chat = update["message"]["from"]["id"]
            is_admin = db.is_admin(user_id)
            is_search = db.is_search(user_id)
            if text == "/start":
                db.add_subscriber(user_id)
                send_message("Добро пожаловать в новостной бот. Отправьте команду /search и любой текст, я постараюсь найти новости.", chat)
            elif text == "/search":
                db.update_search_status_subscriber(user_id, 1) # Обновим статус пользователю, если он выбрал поиск
                send_message("Поиск по новостям, введите поисковую фразу:", chat)
            elif text == "/feed":
                if is_admin:
                     send_message("Список новостных лент", chat)
                else:
                    continue
            elif text.startswith("/"):
                continue
            else:
                if is_search:
                    try:
                        news = db.search_news(text)
                        if len(news) > 0:
                            for item in news:
                                message = """*{}*\n{}\n{}""".format(item[0], item[1], item[2])
                                send_message(message, chat)
                        else:
                            message = "Ничего не найдено по данному запросу. Попробуйте его уточнить"
                            send_message(message, chat)
                    except:
                        message = "Ничего не найдено по данному запросу. Попробуйте его уточнить"
                        send_message(message, chat)
                else:
                    message = "Введите команду /search для поиска новостей"
                    send_message(message, chat)
        except expression as e:
            print(e)

# Функция принимает два параметра chat_id - идентификатор чата и text - сообщение которое мы отправляем.
def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


# Функция для работы с клавиатурой
def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def main():
    last_update_id = None
    db.setup()  # Инициализация БД
    #feed.init() # Запуск парсинга новостных лент
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        
        # Запрашиваем новые сообщения один раз в секунду
        time.sleep(1)

if __name__ == "__main__":
    main()