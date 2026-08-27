# на будущее - https://habr.com/ru/news/1059556/
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

    # создаю датафрейм, в который буду класть юзеров, которые используют бота
    users_statuses_df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    # ЕСЛИ ДВА ЧЕЛОВЕКА НАПИШУТ В ОДИН МОМЕНТ, ТО У КОГО-ТО НЕ ПОЯВИТСЯ ЗАПИСЬ (посмотреть про mutex)
    # если датафрейм пустй, то есть юзер нажал /start впервые
    if users_statuses_df.empty:

        # записываю инфу про юзера
        users_statuses_data = [
            {
                'user_id': message_user,
                'status': 'active'
            }
        ]

        # создаю датафрейм с инфой про юзера, чтобы потом положить в базу
        users_statuses_data_df = pd.DataFrame(data=users_statuses_data)

        # кладу в базу
        users_statuses_data_df.to_sql('users_statuses', con=db, index=False, if_exists='append')

        # отписываюсь юзеру
        bot.reply_to(
            message,
            'Привет! Этот бот будет писать тебе и спрашивать, как твои дела. '
            'Писать он будет 3 раза в день.')

    # если юзер не новый, но у него неактивный статус
    elif users_statuses_df['status'][0] != 'active':

        # сохраняем новый статус юзера
        with db.connect() as conn:
            conn.execute(
                text("UPDATE users_statuses SET status = :status WHERE user_id = :id"),
                {"status": "active", "id": message_user}
            )
            conn.commit()

        # отписываюсь юзеру
        bot.reply_to(
            message,
            'Привет! Ты снова активировал бота. '
            'Теперь он будет писать тебе 3 раза в день.')

    # если юзер активен, но прописал /start еще раз
    else:
        bot.reply_to(
            message,
            'У тебя активный статус, ты получаешь сообщения.')


# обработка команды stop
@bot.message_handler(commands=['stop'])
# определяю функцию, которая отвечает на команду stop
def stop(message):

    # создаю переменную с айди юезра
    message_user = message.from_user.id

    # загружаю датафрейм, в который буду класть юзеров, которые используют бота
    users_statuses_df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    # если датафрейм пустой, то есть юзера нет в базе
    if users_statuses_df.empty:
        # отправляем понятный посыл
        bot.reply_to(
            message,
            'Чтобы что-то остановить, нужно сначала начать.')

    # если актуальный статус активный, то меняем его на stop
    elif users_statuses_df['status'][0] == 'active':

        # сохраняем новый статус юзера
        with db.connect() as conn:
            conn.execute(
                text('UPDATE users_statuses SET status = :status WHERE user_id = :id'),
                {"status": "stop", "id": message_user}
            )
            conn.commit()

        # отписываемся юзеру
        bot.reply_to(
            message,
            'Все с тобой понятно, закругляемся.')

    # если у юзера неактивный статус, то отписываемся
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

    # загружаю данные юзера, чтобы проверить его активность
    users_statuses_df = pd.read_sql_query(f'select * from users_statuses where user_id = {message_user}', con=db)

    # если юзера нет в базе, то отписываюсь об этом
    if users_statuses_df.empty:
        bot.reply_to(
            message,
            'Тебя нет в списках, пропиши /start, чтобы получать вопросы.'
        )
        return

    # если у юзера неактивный статус, то отписываюсь об этом
    elif users_statuses_df['status'][0] == 'stop':
        bot.reply_to(
            message,
            'Мы прекратили общение. Чтобы начать его заново, пропиши /start.'
        )
        return

    # загружаю из базы таблицу с вопросами и ответами
    users_answers_df = pd.read_sql_query(f''
                           f'select '
                           f'	* '
                           f'from users_answers '
                           f'where user_id = {message_user} '
                           f'ORDER BY created_dt DESC '
                           f'LIMIT 1'
                           , con=db)

    # если у юзера нет вопросов, то отписываюсь об этом
    if users_answers_df.empty:
        bot.reply_to(
            message,
            'Тебе еще не было вопросов, рано отвечать.'
        )

    # если датафрейм не пустой, то есть юзеру был направлен вопрос, то сохраняю его ответ
    elif users_answers_df['answer_value'][0] is None:
        try:
            # заменяю запятую точкой, если кто-то ошибся
            formatted_value = float(message.text.replace(',', '.'))

        # если ответ не число
        except ValueError:
            bot.reply_to(message, f'Какой ужас, надо было чиселку, а ты написал(а): {message.text}')
            return

        # если ответ не попал в заданный диапазон значений
        if formatted_value  < 0 or formatted_value > 10:

            # отпсываюсь об этом юзеру
            bot.reply_to(message, f'Какой ужас, надо было число от 0 до 10, а ты написал(а): {message.text}')
            return

        # сохраняю ответ юзера в базу
        with db.connect() as conn:
            conn.execute(
                text('UPDATE users_answers SET answer_value = :value WHERE user_id = :id AND created_dt = :date'),
                {"value": formatted_value, "id": message_user, "date": users_answers_df['created_dt'][0]}
            )
            conn.commit()

        # отписываюсь юзеру о сохраненном ответе
        bot.reply_to(
            message,
            f'Записал твой ответ {formatted_value}.'
        )

    # если юзер продолжает спамить
    else:
        # пытаюсь проверить, чтобы поймать ошибку
        try:
            # заменяю запятую точкой, если кто-то ошибся
            formatted_value = float(message.text.replace(',', '.'))

        # если юзер спамит текстом, то объясняю юзеру
        except ValueError:
            bot.reply_to(message, f'Ну чего, ты хочешь меня на хер послать? '
                                  f'Милости просим, давай. Я тебя тогда тоже нахер пошлю. '
                                  f'Ну и чего? Обнимемся, вместе пойдем, да?')
            return

        # если юзер дал нормальный ответ, но продолжает спамить
        bot.reply_to(
            message,
            'Ты уже ответил(а), жди следующий вопрос.'
        )


# определяю функцию, которая будет всем задавать вопрос
def send_question():

    # создаю вопрос
    question = 'Как твои дела по десятибальной школе с десятыми долями?'

    # загружаю датафрейм с активными юзерами
    users_statuses_df = pd.read_sql_query("select * from users_statuses where status = 'active'", con=db)

    # прохожу по каждому активному юзеру
    for user in users_statuses_df['user_id']:

        # отправляю юзеру вопрос
        bot.send_message(chat_id=user, text=question)

        # сохраняю ответ юзера на вопрос
        with db.connect() as conn:
            conn.execute(
                text('INSERT INTO users_answers (user_id, created_dt) VALUES (:user_id,:date)'),
                {"user_id": user, "date": datetime.datetime.now()}
            )
            conn.commit()


# создаю расписание отправки сообщений
scheduler = BackgroundScheduler()

# создаю три времени, в которые бот будет писать сообщение
trigger_times = [
    CronTrigger(hour=10, minute=00, second=00, timezone=pytz.timezone("Europe/Moscow")),
    CronTrigger(hour=16, minute=00, second=00, timezone=pytz.timezone("Europe/Moscow")),
    CronTrigger(hour=22, minute=00, second=00, timezone=pytz.timezone("Europe/Moscow"))
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