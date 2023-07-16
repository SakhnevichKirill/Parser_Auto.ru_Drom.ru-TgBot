import os
import json
import telebot
from typing import Optional
from dotenv import load_dotenv
from telebot import types


config = load_dotenv(".env")
bot = telebot.TeleBot(os.getenv("telegram_bot_token"))

json_path = "./data.json"

off_markup = types.ReplyKeyboardRemove(selective=False)

start_msg = "*Выберите фильтр*"

menu_btn = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
itembtn1 = types.KeyboardButton("/change_top_price")
menu_btn.add(itembtn1)


def update_global_max_price():
    chat_ids = get_chat_ids()
    max_chat_price = 0
    for id in chat_ids:
        chat_price = get_chat_id_price(id)
        if chat_price > max_chat_price:
            max_chat_price = chat_price

    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file
    data["global_max_price"] = max_chat_price
    print("update_global_max_price", max_chat_price)
    ## Save our changes to JSON file
    jsonFile = open(json_path, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


def get_global_max_price() -> int:
    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file
    return int(data["global_max_price"])


def update_chat_id(new_id: str):
    new_id = str(new_id)
    print("update_chat_id", new_id)
    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file

    ## Working with buffered content
    chat_ids: dict = data["chat_ids"]
    new_id_value = chat_ids.get(new_id)
    if new_id_value:
        pass
    else:
        chat_ids[new_id] = {"price": get_global_max_price()}
    data["chat_ids"] = chat_ids

    ## Save our changes to JSON file
    jsonFile = open(json_path, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


def update_chat_price(new_id: str, price: str):
    new_id = str(new_id)
    price = str(price)
    print(f"chat_id {new_id} update_price: {price}")

    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file

    ## Working with buffered content
    chat_ids: dict = data["chat_ids"]
    new_id_value: dict = chat_ids.get(new_id)
    if new_id_value:
        new_id_value["price"] = price
        chat_ids[new_id] = new_id_value
    else:
        chat_ids[new_id] = {"price": price}
    data["chat_ids"] = chat_ids

    ## Save our changes to JSON file
    jsonFile = open(json_path, "w+")
    jsonFile.write(json.dumps(data))
    jsonFile.close()


def get_chat_ids():
    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file

    ## Working with buffered content
    return data["chat_ids"]


def get_chat_id_price(new_id: str) -> int:
    new_id = str(new_id)
    jsonFile = open(json_path, "r")  # Open the JSON file for reading
    data = json.load(jsonFile)  # Read the JSON into the buffer
    jsonFile.close()  # Close the JSON file

    ## Working with buffered content
    chat_ids: dict = data["chat_ids"]
    new_id_value: dict = chat_ids.get(new_id)
    return int(new_id_value["price"])


@bot.message_handler(commands=["start"])
def start(message) -> None:
    try:
        update_chat_id(message.chat.id)
        bot.send_message(
            message.chat.id, start_msg, reply_markup=menu_btn, parse_mode="MARKDOWN"
        )
    except Exception as e:
        bot.reply_to(message, f"{e}")


@bot.message_handler(commands=["change_top_price"])
def change_top_price(message) -> None:
    try:
        msg = bot.send_message(
            message.chat.id,
            "Укажите предельную цену",
            reply_markup=off_markup,
            parse_mode="MARKDOWN",
        )
        bot.register_next_step_handler(msg, setup_top_price)

    except Exception as e:
        bot.reply_to(message, f"{e}")


def setup_top_price(message):
    try:
        top_price = message.text
        update_chat_price(message.chat.id, top_price)
        update_global_max_price()
        bot.send_message(
            message.chat.id,
            f"Предельная цена обновлена: {top_price}",
            reply_markup=menu_btn,
            parse_mode="MARKDOWN",
        )

    except Exception as e:
        bot.reply_to(message, f"{e}")


import re


def send_ad(
    href: str,
    name: str,
    price: str,
    details: str,
    service: str,
    milage: Optional[str] = None,
    year: Optional[str] = None,
    modification_info: Optional[str] = None,
):
    price = price.replace("\n", "; ")
    details = details.replace("\n", "; ")
    ad_msg = f"""
*Название:* [{name}]({href})
*Цена:* {price}
*Краткое описание:* {details}
*Сервис:* {service}
*Пробег:* {milage if milage is not None else "N/A"}
*Год:* {year if year is not None else "N/A"}
*Технические характеристики:* {modification_info if modification_info is not None else "N/A"}
"""
    chat_ids = get_chat_ids()
    for id in chat_ids:
        chat_price = get_chat_id_price(id)
        end_index = price.find("₽")

        price_arr = re.findall(r"\d+", price[:end_index])
        int_price = int("".join(price_arr))
        print(int_price, "<", chat_price)
        if int_price < chat_price:
            bot.send_message(
                id, ad_msg, reply_markup=off_markup, parse_mode="MarkdownV2"
            )


def main():
    bot.polling(none_stop=True)


def escape_reserved(msg):
    escapes = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for escape in escapes:
        msg = msg.replace(f"{escape}", f"\{escape}")
    return msg


if __name__ == "__main__":
    main()
