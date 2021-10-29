from pymongo import MongoClient
import telebot
from telebot import types

bot = telebot.TeleBot("2057680629:AAFk8KVaoU2_w3QggoSOXZSA6YmMTPIMhrA")

client = MongoClient(
    "mongodb+srv://andrew:admin@cluster0.5eqyk.mongodb.net/telegram_bot_db?retryWrites=true&w=majority")
db = client.telegram_bot_db
notes = db.notes

is_requesting = False
is_entering = False
is_deleting = False
voice = ""


def get_markup_names():
    res = list(notes.find({}, {'name': 1, '_id': 0}))
    if len(res) > 0:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        i = 0
        while i < len(res):
            if i != len(res) - 1:
                markup.row(types.KeyboardButton(res[i]['name']), types.KeyboardButton(res[i + 1]['name']))
            else:
                markup.row(types.KeyboardButton(res[i]['name']))
            i += 2
        return markup
    else:
        return 0


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(chat_id=message.chat.id, text="I am notes bot")


@bot.message_handler(commands=['notes'])
def get_notes_for_request(message):
    global is_requesting
    markup = get_markup_names()
    if markup == 0:
        bot.send_message(chat_id=message.chat.id, text="Nothing found")
    else:
        bot.send_message(chat_id=message.chat.id, text="Chose required note",
                         reply_markup=markup)
        is_requesting = True


@bot.message_handler(commands=['delete'])
def get_notes_for_delete(message):
    global is_deleting
    markup = get_markup_names()
    if markup == 0:
        bot.send_message(chat_id=message.chat.id, text="Nothing found")
    else:
        bot.send_message(chat_id=message.chat.id, text="Chose required note",
                         reply_markup=markup)
        is_deleting = True


@bot.message_handler(content_types=['voice'])
def voice(message):
    global voice, is_entering
    voice = message.voice.file_id
    bot.send_message(chat_id=message.chat.id, text='Enter a name for note')
    is_entering = True


@bot.message_handler(content_types=['text'])
def name(message):
    global is_requesting, is_entering, voice, is_deleting
    if is_entering:
        notes.insert_one({'voice': voice, 'name': message.text})
        bot.send_message(chat_id=message.chat.id, text='Note successfully created')
        is_entering = False
        voice = ""
    elif is_requesting:
        note = notes.find_one({'name': message.text})
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_voice(chat_id=message.chat.id, voice=note['voice'],
                       reply_markup=markup)
        is_requesting = False
    elif is_deleting:
        notes.delete_one({'name': message.text})
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(chat_id=message.chat.id, text='Note successfully deleted',
                         reply_markup=markup)
        is_deleting = False


bot.infinity_polling()
