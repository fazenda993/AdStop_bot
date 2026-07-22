import os
from threading import Thread
import time
from flask import Flask
from telebot import TeleBot, types

# === НАСТРОЙКИ ВЕБ-СЕРВЕРА ДЛЯ БЕСПЛАТНОГО ХОСТИНГА ===
app = Flask("")


@app.route("/")
def home():
  return "AdManager Bot активен и работает 24/7!"


def run_web_server():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# === НАСТРОЙКИ БОТА ===
TOKEN = "8975791580:AAES9gbrudFU_cGwVk3AuP8azFzW-CxrP3c"
bot = TeleBot(TOKEN)

# Временная база данных заказов в памяти
user_orders = {}

# Прайс-лист услуг
PRICES = {
    "1_24": {"name": "1 час топа / 24 часа в ленте", "price": 500},
    "2_48": {"name": "2 часа топа / 48 часов в ленте", "price": 800},
    "no_delete": {"name": "Без удаления (Навсегда)", "price": 1500},
}


# --- КОМАНДА /START ---
@bot.message_handler(commands=["start"])
def start_cmd(message):
  kb = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "📢 Купить рекламу", callback_data="buy_ad"
  )
  btn2 = types.InlineKeyboardButton(
      "ℹ️ Как это работает?", callback_data="help_info"
  )
  kb.add(btn1, btn2)

  bot.send_message(
      message.chat.id,
      f"👋 **Привет, {message.from_user.first_name}!**\n\n"
      "Я автоматический менеджер рекламы.\n"
      "С моей помощью вы можете забронировать и выложить рекламный пост за пару"
      " кликов!\n\n"
      "Выберите действие ниже:",
      parse_mode="Markdown",
      reply_markup=kb,
  )


# --- ОБРАБОТЧИК КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  chat_id = call.message.chat.id

  if call.data == "buy_ad":
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, info in PRICES.items():
      btn = types.InlineKeyboardButton(
          f"{info['name']} — {info['price']} RUB",
          callback_data=f"select_{code}",
      )
      kb.add(btn)

    bot.edit_message_text(
        "📊 **Выберите формат размещения:**",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb,
    )

  elif call.data.startswith("select_"):
    tariff_code = call.data.split("_", 1)[1]
    tariff_info = PRICES.get(tariff_code)

    user_orders[call.from_user.id] = {
        "tariff": tariff_info["name"],
        "price": tariff_info["price"],
    }

    bot.send_message(
        chat_id,
        f"✅ Вы выбрали: **{tariff_info['name']}**\n"
        f"К оплате: **{tariff_info['price']} RUB**\n\n"
        "✏️ **Отправьте текст рекламного поста** (можно с фото или ссылкой):",
        parse_mode="Markdown",
    )
    bot.register_next_step_handler(call.message, get_post_content)

  elif call.data == "help_info":
    bot.send_message(
        chat_id,
        "💡 **Инструкция:**\n"
        "1. Выберите подходящий тариф размещения.\n"
        "2. Отправьте готовый пост для публикации.\n"
        "3. Оплатите счет удобным способом.\n"
        "4. Бот сам выложит пост в свободное время!",
    )

  elif call.data.startswith("pay_confirm_"):
    order_user_id = int(call.data.split("_")[2])
    order = user_orders.get(order_user_id)

    if order:
      bot.send_message(
          chat_id,
          "🎉 **Оплата успешно принята!**\nВаш пост забронирован и будет"
          " опубликован в ближайшее время.",
          parse_mode="Markdown",
      )
    else:
      bot.send_message(chat_id, "Ошибка: Заказ не найден.")


# --- ПОЛУЧЕНИЕ ТЕКСТА ПОСТА ---
def get_post_content(message):
  user_id = message.from_user.id
  if user_id in user_orders:
    user_orders[user_id]["post_text"] = message.text

    kb = types.InlineKeyboardMarkup()
    btn_pay = types.InlineKeyboardButton(
        "💳 Оплатить (Тестовая оплата)",
        callback_data=f"pay_confirm_{user_id}",
    )
    kb.add(btn_pay)

    bot.send_message(
        message.chat.id,
        f"📝 **Ваш пост принят!**\n\n"
        f"**Тариф:** {user_orders[user_id]['tariff']}\n"
        f"**Сумма:** {user_orders[user_id]['price']} RUB\n\n"
        f"**Текст поста:**\n{message.text}\n\n"
        "Нажмите кнопку ниже для проведения оплаты:",
        parse_mode="Markdown",
        reply_markup=kb,
    )


# --- ЗАПУСК СЕРВЕРА И БОТА ---
Thread(target=run_web_server).start()

print("AdManager Bot запущен...")
bot.infinity_polling()
    
