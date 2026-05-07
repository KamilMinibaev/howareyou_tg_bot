import telebot

import os
from dotenv import load_dotenv

import datetime

import pandas as pd

import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# загружаю данные для токена бота
load_dotenv()

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
	bot.reply_to(
		message,
		'Привет! Этот бот будет писать тебе и спрашивать, как твои дела. '
		'Писать он будет 3 раза в день.')

	# загружаю датафрейм, в который буду класть юзеров, которые используют бота
	df = pd.read_csv('data/user_statuses.csv')

	# создаю переменную с человеческим форматом даты
	message_date = datetime.datetime.fromtimestamp(message.date)

	# создаю переменную с айди юезра для записи в историю
	message_user = message.from_user.id

	# записываю инфу про юзера
	user_statuses_data = [
		{
			'user_id': message_user,
			'active_from': message_date,
			'status': 'active'
		}
	]

	# ЕСЛИ ДВА ЧЕЛОВЕКА НАПИШУТ В ОДИН МОМЕНТ, ТО У КОГО-ТО НЕ ПОЯВИТСЯ ЗАПИСЬ (посмотреть про mutex)
	# если юзер новый, то есть нажал /start впервые
	if message_user not in df['user_id'].values: #кстати, операция сложная, сортировки еще нет
		# создаю датафрейм с инфой про юзера, чтобы потом объединить с основным файлом
		user_statuses_data_df = pd.DataFrame(data=user_statuses_data)

		# обновляю исходный датафрейм
		user_statuses = pd.concat([df, user_statuses_data_df])

		# сохраняю
		user_statuses.to_csv('data/user_statuses.csv', index=False)

		# создаю файл для пользователя, если пользователь впервые активировал бота
		user_answer = pd.DataFrame(columns=['user_id', 'date', 'value'])

		# сохраняю новый файл для нового юзера
		user_answer.to_csv(f'data/{message_user}_answer.csv', index=False)

	# если юзер не новый
	else:
		# если актуальный статус активный, то ничего не меняем
		if df.query(f'user_id == {message_user}').status.to_list() == ['active']:
			pass

		# если неактивный статус, то меняем на активный, ведь прописали /start
		else:
			df.loc[df.user_id == message_user, 'status'] = 'active'

			# сохраняем новый статус юзера
			df.to_csv('data/user_statuses.csv', index=False)


# обработка команды stop
@bot.message_handler(commands=['stop'])
# определяю функцию, которая отвечает на команду stop
def stop(message):
	# загружаю датафрейм, в который буду класть юзеров, которые используют бота
	df = pd.read_csv('data/user_statuses.csv')

	# создаю переменную с айди юезра для записи в историю
	message_user = message.from_user.id

	# если актуальный статус активный, то меняем его на stop
	if df.query(f'user_id == {message_user}').status.to_list() == ['active']:
		df.loc[df.user_id == message_user, 'status'] = 'stop'

		# сохраняем новый статус юзера
		df.to_csv('data/user_statuses.csv', index=False)

		# отправляем сообщение о завершении
		bot.reply_to(
			message,
			'Все с тобой понятно, закругляемся)')

	else:
		# отправляем понятный посыл
		bot.reply_to(
			message,
			'Чтобы что-то остановить, нужно сначала начать.')




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

	# загружаю датафрейм, в который буду класть юзеров, которые используют бота
	df = pd.read_csv('data/user_statuses.csv')

	# если актуальный статус активный, то бот сохраняет ответы юзера
	if df.query(f'user_id == {message_user}').status.to_list() == ['active']:

		try:
			# заменяю запятую точкой, если кто-то ошибся
			formatted_value = float(message.text.replace(',', '.'))

			# проверяю значение числа на попадание в разрешенный отрезок
			if 0 <= formatted_value <= 10:

				# формирую дикт для добавления его в данные
				data_to_add = [
					{
					'date': f'{message_date}',
					'value': formatted_value
					}
				]

				data_to_add_df = pd.DataFrame(data=data_to_add)

				# открываю существующий файл с ответами юзера
				user_answers_df = pd.read_csv(f'data/{message_user}_answer.csv')

				# объединяю новый ответ со старым ответом
				user_answers_df = pd.concat([user_answers_df, data_to_add_df])

				# объединяю новый ответ со старым ответом
				user_answers_df.to_csv(f'data/{message_user}_answer.csv', index=False)

				# ответ в чат
				bot.reply_to(
					message,
					f'Записал твой ответ = {formatted_value} на дату = {message_date}'
				)

			# если ответ не попал в дозволенный диапазон
			else:
				bot.reply_to(message, f'Какой ужас, надо было число от 0 до 10, а ты написал(а): {message.text}')

		# если ответ не число
		except ValueError:
			bot.reply_to(message, f'Какой ужас, надо было чиселку, а ты написал(а): {message.text}')

	# если статус стоп у юзера, то подсвечиваем ему
	else:
		bot.reply_to(message, 'По моим данным мы прекратили общение, если хочешь возобновить, то пропиши /start')

# определяю функцию, которая будет всем задавать вопрос
def send_question():

	# создаю вопрос
	question = 'Как твои дела по десятибальной школе с десятыми долями?'

	# беру данные юзеров
	users_data_df = pd.read_csv('data/user_statuses.csv')

	# оставляю только тех, у кого активный статус
	users_active_data_df = users_data_df[users_data_df['status'] == 'active']

	# прохожу по каждому активному юзеру
	for user in users_active_data_df['user_id']:

		# отправляю юзеру вопрос
		bot.send_message(chat_id=user, text=question)


# создаю расписание отправки сообщений
scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Moscow"))

# создаю три времени, в которые бот будет писать сообщение
trigger_times = [
	CronTrigger(hour=23, minute=37, second=10),
	CronTrigger(hour=23, minute=37, second=20),
	CronTrigger(hour=23, minute=37, second=30)
	]

# для каждой точки отправляю сообщение
for trigger in trigger_times:
	scheduler.add_job(
		send_question,
		trigger=trigger
	)

# запускаю расписание
scheduler.start()

# запускаю бота
bot.infinity_polling()
