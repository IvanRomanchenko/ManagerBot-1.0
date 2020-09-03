import time
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, URL, SECRET, GROUP_ID
from settings_db import *


bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

bot.remove_webhook()
bot.set_webhook(url=URL)

app = Flask(__name__)

@app.route('/' + SECRET, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200
    

def is_admin(func):
    """ Декоратор для верификации администраторов """
    def wrap(message):
        stat = lambda x_id: requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember", params = {'chat_id': {int(GROUP_ID)}, 'user_id': {int(x_id)}}).json()['result']['status']
        user_stat = stat(message.from_user.id)
        bot_stat = stat(<id бота>)        
        if user_stat == 'creator' or user_stat == 'administrator':
            if bot_stat == 'administrator':
                func(message)
            else:
                bot.send_message(message.from_user.id, "Вы не предоставили мне права администратора этой группы.")
        else:
            bot.send_message(message.from_user.id, "Вы не являетесь администратором этой группы.")        
    return wrap


def del_mess_in_group(message):
    """ Удаляет сообщения-комманды, если они не в приватном чате """
    if message.chat.type != 'private':
        bot.delete_message(message.chat.id, message.message_id)
        

@bot.message_handler(commands = ['start', 'help'])
def start(message):
    """ Приветствие с разъяснениями """
    del_mess_in_group(message)

    bot.send_message(message.from_user.id, f"\
                    \nПриветствую Вас, {message.from_user.first_name} {message.from_user.last_name}!\
                    \nМеня зовут {bot.get_me().first_name}.\
                    \nЯ - незаменимый помощник администраторов телеграм-групп.\
                    \n\
                    \nДобавьте меня в свою группу и предоставьте права администратора.\
                    \nПосле этого мы можем приступить к настройке моей работы.\
                    \n\nДля настройки введите команду /settings и проследуйте инструкциям.\
                    \n\nЖду не дождусь, когда смогу приступить ☺️")


@bot.message_handler(commands = ['settings'])
@is_admin
def settings(message):
    """ Настройка работы бота в группах """
    del_mess_in_group(message)
    
    markup = InlineKeyboardMarkup(row_width = 1)
    btn1 = InlineKeyboardButton("Настроить ограничение символов в сообщениях", callback_data=f"symbolsLimit")
    btn2 = InlineKeyboardButton("Настроить удаление системных сообщений", callback_data=f"sysMessages")
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "С чего начнём настройку?", reply_markup = markup)  


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """ Обработка ответов """
    if call.data == "symbolsLimit":
        msg = bot.send_message(call.from_user.id, "Введите максимальное допустимое количество символов для сообщений чата:")
        bot.register_next_step_handler(msg, limit_symbols)
        
    elif call.data == "sysMessages":
        markup = InlineKeyboardMarkup(row_width = 2)
        btn1 = InlineKeyboardButton("Да", callback_data=f"delSysOn")
        btn2 = InlineKeyboardButton("Нет", callback_data=f"delSysOff")
        markup.add(btn1, btn2)
        bot.send_message(call.from_user.id, "Удалять все системные сообщения?", reply_markup = markup)

    elif call.data == "delSysOn": # Вкл. удаление системных сообщений
        update_del_sys_messages(GROUP_ID, 1)
        bot.send_message(call.from_user.id, "Теперь я буду удалять все системные сообщения в выбранном чате.")

    elif call.data == "delSysOff": # Выкл. удаление системных сообщений
        update_del_sys_messages(GROUP_ID, 0)  
        bot.send_message(call.from_user.id, "Я больше не буду удалять системные сообщения в выбранном чате.")
    

def limit_symbols(message):
    if message.text.isdigit():
        update_max_symbols(GROUP_ID, int(message.text))
        bot.send_message(message.from_user.id, f"Вы успешно установили ограничение в {message.text} символов.")

    else:
        msg = bot.send_message(message.from_user.id, f"Неверный ввод.\nПожалуйста, введите только число.")
        bot.register_next_step_handler(msg, limit_symbols)


@bot.message_handler(content_types = ['text'])
def limit(message):
    """ Ограничивает количество символов в сообщениях """
    if len(message.text) > read_max_symbols(GROUP_ID):
        bot.delete_message(GROUP_ID, message.message_id)
        bot.send_message(GROUP_ID, f"{message.from_user.first_name} {message.from_user.last_name}, Вы превысили лимит символов, попробуйте уменьшить количество текста до {read_max_symbols(GROUP_ID)} символов.\n\nЭто сообщение удалится через 20 секунд.\n\n{message.text}")
        time.sleep(20) # Удаление через 20 секунд
        bot.delete_message(GROUP_ID, message.message_id + 1)


@bot.message_handler(content_types = ['new_chat_members', 'left_chat_member', 'pinned_message'])
def del_system_messages(message):
    """ Удаляет системные сообщения (о вступлении в группу, удалении из группы, закреплении сообщения) """
    if read_del_sys_messages(GROUP_ID) == 1:
        bot.delete_message(GROUP_ID, message.message_id)
