import json

import telebot

import os
from dotenv import load_dotenv

import datetime

# загружаю данные для токена бота
load_dotenv()

# создаю переменную с токеном бота
token = os.getenv('TELEGRAM_BOT_TOKEN')

# создаю объект, класс которого ТелеБот
bot = telebot.TeleBot(token)


# обработка команд start, help
@bot.message_handler(commands=['start', 'help'])
# определяю функцию, которая отвечает на команды start и help
def send_welcome(message):
	bot.reply_to(message, 'Howdy, how are you doing?')


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