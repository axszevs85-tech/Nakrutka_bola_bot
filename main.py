import telebot
from telebot import types
import os 
from dotenv import load_dotenv
# Bot tokenini kiriting
API_TOKEN = '8987059390:AAEzlSM3zUxToiTpJqpuRu8dbXjlgj3WWcU'
bot = telebot.TeleBot(API_TOKEN)

# Foydalanuvchilar ma'lumotlari saqlanadigan lug'at
users = {}

# Narxlar va konversiya
gnom_prices = {
    1: 500,
    2: 1000,
    3: 2000,
    4: 2500,
    5: 5500
}

currency_conversion = 10  # 100 tanga = 10 gold

# Foydalanuvchini boshlang'ich holat bilan yaratish
def create_user(user_id):
    users[user_id] = {
        'tanga': 1000,  # Dastlabki tangalar
        'gold': 0,
        'gnom': 0
    }

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        create_user(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Gnom sotib olish"), types.KeyboardButton("Pul kiritish"), types.KeyboardButton("Pul chiqarish"), types.KeyboardButton("Holat"))

    bot.send_message(message.chat.id, "Salom! Sizning tangalaringiz: 1000. Iltimos, biror bir variantni tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Gnom sotib olish")
def buy(message):
    user_id = message.from_user.id
    if user_id not in users:
        create_user(user_id)

    msg = "Gnomlarni sotib olish uchun narxlar:\n"
    for gnom, price in gnom_prices.items():
        msg += f"{gnom} gnom - {price} tanga\n"
    msg += "Qaysi gnomni sotib olmoqchisiz? (1-5)\n"
    
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda message: message.text.isdigit() and 1 <= int(message.text) <= 5)
def purchase_gnome(message):
    user_id = message.from_user.id
    gnome_choice = int(message.text)

    user = users[user_id]
    price = gnom_prices[gnome_choice]

    if user['tanga'] >= price:
        user['tanga'] -= price
        user['gnom'] += gnome_choice
        bot.send_message(message.chat.id, f"Siz {gnome_choice} gnom sotib oldingiz! Sizning tangalaringiz: {user['tanga']}.")
    else:
        bot.send_message(message.chat.id, "Tangalar yetarli emas!")

@bot.message_handler(func=lambda message: message.text == "Pul kiritish")
def add_tanga_prompt(message):
    bot.send_message(message.chat.id, "Qancha tanga kiritmoqchisiz?")

@bot.message_handler(func=lambda message: message.text.isdigit(), content_types=['text'])
def add_tanga(message):
    user_id = message.from_user.id
    tanga_amount = int(message.text)

    user = users[user_id]
    user['tanga'] += tanga_amount
    bot.send_message(message.chat.id, f"Sizning tangalaringiz: {user['tanga']}.")

@bot.message_handler(func=lambda message: message.text == "Pul chiqarish")
def withdraw_tanga_prompt(message):
    bot.send_message(message.chat.id, "Qancha tanga chiqarishni xohlaysiz?")

@bot.message_handler(func=lambda message: message.text.isdigit(), content_types=['text'])
def withdraw_tanga(message):
    user_id = message.from_user.id
    tanga_amount = int(message.text)

    user = users[user_id]
    if user['tanga'] >= tanga_amount:
        user['tanga'] -= tanga_amount
        bot.send_message(message.chat.id, f"Sizning tangalaringiz: {user['tanga']}. Pul chiqarildi!")
    else:
        bot.send_message(message.chat.id, "Tangalar yetarli emas!")

@bot.message_handler(func=lambda message: message.text == "Holat")
def status(message):
    user_id = message.from_user.id
    if user_id not in users:
        create_user(user_id)

    user = users[user_id]
    bot.send_message(message.chat.id, f"Sizning tangalaringiz: {user['tanga']}, gold: {user['gold']}, gnom: {user['gnom']}.")

# Botni ishga tushirish
bot.polling()
