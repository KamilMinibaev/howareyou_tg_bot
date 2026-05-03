import json

import telebot

import os
from dotenv import load_dotenv

import datetime

import pandas as pd
from tornado.escape import utf8

# загружаю данные для токена бота
load_dotenv()

# создаю переменную с токеном бота
token = os.getenv('TELEGRAM_BOT_TOKEN')

# создаю объект, класс которого ТелеБот
bot = telebot.TeleBot(token)


# обработка команды start
@bot.message_handler(commands=['start'])
# определяю функцию, которая отвечает на команды start и help
def send_welcome(message):
	bot.reply_to(
		message,
		'Привет! Этот бот будет писать тебе и спрашивать, как твои дела. '
		'Писать он будет 3 раза в день.')

	# загружаю датафрейм, в который буду класть юзеров, которые используют бота
	df = pd.read_csv('data/user_status.csv')

	# создаю переменную с человеческим форматом даты
	message_date = datetime.datetime.fromtimestamp(message.date)

	# создаю переменную с айди юезра для записи в историю
	message_user = message.from_user.id

	# ВОТ ТУТ ДОЛЖНА БЫТЬ ПРОВЕРКА НА ТО, ЕСТЬ ЛИ ЮЗЕР ИЗ СООБЩЕНИЯ В ДАННЫХ И КАКОЙ У НЕГО СТАТУС
	# ЕСЛИ НЕТ, ТО СОЗДАЕМ ЕМУ СТРОЧКУ
	# ЕСЛИ ЕСТЬ, ТО СМОТРИМ ЕГО СТАТУС
	# ЕСЛИ СТАТУС АКТИВ, ТО НИЧЕГО НЕ ДЕЛАЕМ
	# ЕСЛИ СТАТУС ДЕАКТИВ, ТО АКТИВИРУЕМ, ВЕДЬ ОН НАЖАЛ СТАРТ

	# записываю инфу про юзера
	user_data = [
		{
		'user_id': message_user,
		'active_from': message_date,
		'status': 'active'
		}
	]

	# создаю датафрейм с инфой про юзера, чтобы потом объединить с основным файлом
	user_data_df = pd.DataFrame(data=user_data)

	# обновляю исходный датафрейм
	df = pd.concat([df, user_data_df])

	# сохраняю
	df.to_csv('data/user_status.csv', index=False)

	print(df.head())


# обработка полученных сообщений
@bot.message_handler(func=lambda message: True)
def how_are_you(message):
	"""
	функция проверяет, является ли сообщение числом, сохраняет полученный ответ при успехе и отправляет в чат
	"""

	# создаю переменную с человеческим форматом даты
	message_date = datetime.datetime.fromtimestamp(message.date)

	# создаю переменную с айди юезра для записи в историю
	message_user = message.from_user.id

	try:
		formatted_value = float(message.text.replace(',', '.'))

		if 0 <= formatted_value <= 10:

			# формирую дикт для добавления его в данные
			data_to_json = {
				'user_id': message_user,
				'date': f'{message_date}',
				'value': formatted_value
			}

			# беру актуальные данные
			with open('data/user_answers.json') as f:
				d = json.load(f)
				print(d)

			# добавляю актуальное сообщени в list, который я вытащил из json
			d.append(data_to_json)

			# кладу обновленный list в json файл
			with open('data/user_answers.json', 'w') as f:
				json.dump(d, f, indent=4)

			bot.reply_to(
				message,
				f'Записал твой ответ = {formatted_value} на дату = {message_date}'
			)

		else:
			bot.reply_to(message, f'Какой ужас, надо было число от 0 до 10, а ты написал(а): {message.text}')

	except ValueError:
		bot.reply_to(message, f'Какой ужас, надо было чиселку, а ты написал(а): {message.text}')

# запускаю бота
bot.infinity_polling()