import telebot

import os

import datetime

import pandas as pd

import pytz

from how_are_you_bot_db import db, migrate_database

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

migrate_database()

# создаю переменную с токеном бота
token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    raise ValueError('Не нашел token')

# создаю объект, класс которого ТелеБот
bot = telebot.TeleBot(token)


# обработка команды start
@bot.message_handler(commands=['start'])
# определяю функцию, которая отвечает на команду start
def start(message):
    # создаю переменную с айди юезра для записи в историю
    message_user = message.from_user.id

    # загружаю датафрейм, в который буду класть юзеров, которые используют бота
    df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    # ЕСЛИ ДВА ЧЕЛОВЕКА НАПИШУТ В ОДИН МОМЕНТ, ТО У КОГО-ТО НЕ ПОЯВИТСЯ ЗАПИСЬ (посмотреть про mutex)
    # если юзер новый, то есть нажал /start впервые
    if df.empty:

        # записываю инфу про юзера
        users_statuses_data = [
            {
                'user_id': message_user,
                'status': 'active'
            }
        ]

        # создаю датафрейм с инфой про юзера, чтобы потом объединить с основным файлом
        users_statuses_data_df = pd.DataFrame(data=users_statuses_data)

        users_statuses_data_df.to_sql('users_statuses', con=db, index=False, if_exists='append')

        bot.reply_to(
            message,
            'Привет! Этот бот будет писать тебе и спрашивать, как твои дела. '
            'Писать он будет 3 раза в день.')

    # если юзер не новый
    elif df['status'][0] != 'active':

        # сохраняем новый статус юзера
        with db.connect() as conn:
            conn.execute(
                text("UPDATE users_statuses SET status = :status WHERE user_id = :id"),
                {"status": "active", "id": message_user}
            )
            conn.commit()

        bot.reply_to(
            message,
            'Привет! Ты снова активировал бота. '
            'Теперь он будет писать тебе 3 раза в день.')

    else:
        bot.reply_to(
            message,
            'У тебя активный статус, ты получаешь сообщения.')


# обработка команды stop
@bot.message_handler(commands=['stop'])
# определяю функцию, которая отвечает на команду stop
def stop(message):
    # создаю переменную с айди юезра для записи в историю
    message_user = message.from_user.id

    # загружаю датафрейм, в который буду класть юзеров, которые используют бота
    df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    if df.empty:
        # отправляем понятный посыл
        bot.reply_to(
            message,
            'Чтобы что-то остановить, нужно сначала начать.')

    # если актуальный статус активный, то меняем его на stop
    # если юзер не новый
    elif df['status'][0] == 'active':

        # сохраняем новый статус юзера
        with db.connect() as conn:
            conn.execute(
                text('UPDATE users_statuses SET status = :status WHERE user_id = :id'),
                {"status": "stop", "id": message_user}
            )
            conn.commit()

        bot.reply_to(
            message,
            'Все с тобой понятно, закругляемся.')

    else:
        bot.reply_to(
            message,
            'Ты и так не получаешь сообщения, пропиши /start для возобновления.')


# обработка полученных сообщений
@bot.message_handler(func=lambda message: True)
def how_are_you(message):
    """
    функция проверяет, является ли сообщение числом, сохраняет полученный ответ при успехе и отправляет в чат
    """

    # создаю переменную с айди юезра для записи в историю
    message_user = message.from_user.id

    df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    if df.empty:
        bot.reply_to(
            message,
            'Тебя нет в списках, пропиши /start, чтобы получать вопросы.'
        )
        return

    elif df['status'][0] == 'stop':
        bot.reply_to(
            message,
            'Мы прекратили общение. Чтобы начать его заново, пропиши /start.'
        )
        return

    df = pd.read_sql_query(f''
                           f'select '
                           f'	* '
                           f'from user_answers '
                           f'where user_id = {message_user} '
                           f'ORDER BY created_dt DESC '
                           f'LIMIT 1'
                           , con=db)

    if df.empty:
        bot.reply_to(
            message,
            'Тебе еще не было вопросов, рано отвечать.'
        )
    elif df['answer_value'][0] is None:
        try:
            # заменяю запятую точкой, если кто-то ошибся
            formatted_value = float(message.text.replace(',', '.'))

        # если ответ не число
        except ValueError:
            bot.reply_to(message, f'Какой ужас, надо было чиселку, а ты написал(а): {message.text}')
            return

        if formatted_value  < 0 or formatted_value > 10:
            bot.reply_to(message, f'Какой ужас, надо было число от 0 до 10, а ты написал(а): {message.text}')
            return

        with db.connect() as conn:
            conn.execute(
                text('UPDATE user_answers SET answer_value = :value WHERE user_id = :id AND created_dt = :date'),
                {"value": formatted_value, "id": message_user, "date": df['created_dt'][0]}
            )
            conn.commit()

        bot.reply_to(
            message,
            f'Записал твой ответ {formatted_value}.'
        )
    else:
        try:
            # заменяю запятую точкой, если кто-то ошибся
            formatted_value = float(message.text.replace(',', '.'))

        # если ответ не число
        except ValueError:
            bot.reply_to(message, f'Ну чего, ты хочешь меня на хер послать? '
                                  f'Милости просим, давай. Я тебя тогда тоже нахер пошлю. '
                                  f'Ну и чего? Обнимемся, вместе пойдем, да?')
            return

        bot.reply_to(
            message,
            'Ты уже ответил, жди следующий вопрос.'
        )


# определяю функцию, которая будет всем задавать вопрос
def send_question():
    # создаю вопрос
    question = 'Как твои дела по десятибальной школе с десятыми долями?'

    # загружаю датафрейм, в который буду класть юзеров, которые используют бота
    df = pd.read_sql_query("select * from users_statuses where status = 'active'", con=db)

    # прохожу по каждому активному юзеру
    for user in df['user_id']:
        # отправляю юзеру вопрос
        bot.send_message(chat_id=user, text=question)

        # сохраняем новый статус юзера
        with db.connect() as conn:
            conn.execute(
                text('INSERT INTO user_answers (user_id, created_dt) VALUES (:user_id,:date)'),
                {"user_id": user, "date": datetime.datetime.now()}
            )
            conn.commit()


# создаю расписание отправки сообщений
scheduler = BackgroundScheduler()

# создаю три времени, в которые бот будет писать сообщение
trigger_times = [
    CronTrigger(hour=22, minute=38, second=30, timezone=pytz.timezone("Europe/Moscow")),
    CronTrigger(hour=22, minute=19, second=30, timezone=pytz.timezone("Europe/Moscow")),
    CronTrigger(hour=22, minute=20, second=30, timezone=pytz.timezone("Europe/Moscow"))
]

# для каждой точки отправляю сообщение
for trigger in trigger_times:
    scheduler.add_job(
        send_question,
        trigger=trigger
    )

# запускаю расписание
scheduler.start()

bot.infinity_polling()