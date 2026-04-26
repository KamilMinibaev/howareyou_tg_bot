import telebot

import os
from dotenv import load_dotenv

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


# # обработка полученных сообщений
# @bot.message_handler(func=lambda message: True)
# # определяю функцию, которая отвечает на все сообщения моим сообщением
# def echo_all(message):
# 	bot.reply_to(message, message.text)


# обработка полученных сообщений
@bot.message_handler(func=lambda message: True)
# определяю функцию, которая проверяет, является ли сообщение числом
def float_check(message):

	try:
		formatted_value = float(message.text.replace(',', '.'))

		if 0 <= formatted_value <= 10:
			bot.reply_to(message, f'ОТЛИЧНО, принял твой ответ: {message.text}')

		else:
			bot.reply_to(message, f'ПРОЕБАЛИ, надо было число от 0 до 10, а ты написал(а): {message.text}')

	except ValueError:
		bot.reply_to(message, f'ПРОЕБАЛИ, надо было чиселку, а ты написал(а): {message.text}')

# запускаю бота
bot.infinity_polling()