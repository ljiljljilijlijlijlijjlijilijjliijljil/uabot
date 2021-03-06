import logging
import text
import json
from mongodb import mongo_get_index, mongo_receive_cities
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler
import emojis
import math

# Global variables
_cached_city = "Киев"
_cached_city_page = 1

_cached_index_page = 1
_cached_index_dict = {}

def get_token():
    with open("config.json", "r") as config:
        config = json.loads(config.read())
        token = str(config['token'])
        return token


# Basic logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Interaction with Mongo Functions
# TODO: Needs to be separated in the future
def construct_cities_list(cities_list, page_num):
    keyboard = []
    list_len = len(cities_list)
    buttons_per_page = 5
    if list_len <= buttons_per_page:
        for city in cities_list:
            keyboard.append([InlineKeyboardButton(str(city), callback_data=str(city))])

    else:
        # compute first and last indexes
        last_index = page_num * buttons_per_page
        first_index = last_index - buttons_per_page

        # extract the cities for the page
        page_list = cities_list[first_index:last_index]

        # add cities
        for city in page_list:
            keyboard.append([InlineKeyboardButton(str(city), callback_data=str(city))])

        # add navigation footer
        navigation_footer = [InlineKeyboardButton(emojis.encode(":arrow_left:"), callback_data="city_list_back"),
                             InlineKeyboardButton(f"{last_index}/{list_len}", callback_data="do_nothing"),
                             InlineKeyboardButton(emojis.encode(":arrow_right:"), callback_data="city_list_forward")]
        keyboard.append(navigation_footer)
    return keyboard

# ==== Command Handlers ====
# "/start" handler
def start_command(update, context):
    reply_markup = InlineKeyboardMarkup(construct_cities_list(mongo_receive_cities(), 1))
    context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_start,
                             reply_markup=reply_markup)


# "/city" handler
def city_command(update, context):
    reply_markup = InlineKeyboardMarkup(construct_cities_list(mongo_receive_cities(), 1))
    context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_available_cities,
                             reply_markup=reply_markup)


# inline query handler
# By default chooses the city
# Eventually I decided to use it more than once :)
def inline_query_handler(update, context):
    query = update.callback_query
    query.answer()
    global _cached_city_page
    global _cached_index_page
    global _cached_city
    total_pages = math.ceil(len(_cached_index_dict) / 10)
    addresses = list(_cached_index_dict.keys())
    indexes = list(_cached_index_dict.values())
    if str(query.data) == "city_list_back":
        if _cached_city_page <= 1:
            reply = text.txt_zero_page
        else:
            _cached_city_page -= 1
            reply = text.txt_available_cities
        reply_markup = InlineKeyboardMarkup(construct_cities_list(mongo_receive_cities(), _cached_city_page))
        query.edit_message_text(text=reply, reply_markup=reply_markup)

    elif str(query.data) == "city_list_forward":
        _cached_city_page += 1
        reply_markup = InlineKeyboardMarkup(construct_cities_list(mongo_receive_cities(), _cached_city_page))
        query.edit_message_text(text=text.txt_available_cities, reply_markup=reply_markup)

    elif str(query.data) == "index_list_back":
        print("Index Page: " + str(_cached_index_page))
        print("Total Pages: " + str(total_pages))
        if _cached_index_page > 1 :
            _cached_index_page = _cached_index_page - 1
            list_from = int(_cached_index_page) * 10 - 1
            list_until = list_from + 10
            addresses = addresses[list_from:list_until]
            indexes = indexes[list_from:list_until]

            reply_markup = construct_markup_index_list(_cached_index_page, total_pages)
            reply = construct_indexes_list(_cached_city, addresses, indexes)

            query.edit_message_text(text=reply, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    elif str(query.data) == "index_list_forward":
        print("Index Page: " + str(_cached_index_page))
        print("Total Pages: " + str(total_pages))
        if _cached_index_page <= total_pages - 1:
            _cached_index_page += 1
            list_from = int(_cached_index_page-1) * 10
            list_until = list_from + 10
            addresses = addresses[list_from:list_until]
            indexes = indexes[list_from:list_until]

            reply_markup = construct_markup_index_list(_cached_index_page, total_pages)
            reply = construct_indexes_list(_cached_city, addresses, indexes)
            query.edit_message_text(text=reply, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    elif str(query.data) == "do_nothing":
            pass

    elif str(query.data) in mongo_receive_cities():
        _cached_city = str(query.data)
        query.edit_message_text(text=text.txt_city_found)
    else:
        query.edit_message_text(text=text.txt_error)


def construct_indexes_list(_cached_city, addresses, indexes):
    reply = f'Город:  <b>{_cached_city}</b>\n'
    for x in range(0, len(addresses)):
        reply += f"\n<i>{str(addresses[x])}</i>: <b>{str(indexes[x])}</b>"
    return reply


def construct_markup_index_list(_cached_index_page, total_pages):
    keyboard = [[InlineKeyboardButton(emojis.encode(":arrow_left:"), callback_data="index_list_back"),
                 InlineKeyboardButton(f"{_cached_index_page}/{total_pages}", callback_data="do_nothing"),
                 InlineKeyboardButton(emojis.encode(":arrow_right:"), callback_data="index_list_forward")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


# text_handler
# By default needs to search for index by user input
def index_command(update, context):
    user_input = str(update.message.text)
    global _cached_city
    global _cached_index_dict
    global _cached_index_page
    _cached_index_page = 1
    _cached_index_dict = mongo_get_index(user_input, _cached_city)
    total_pages = math.ceil(len(_cached_index_dict) / 10)
    addresses = list(_cached_index_dict.keys())
    indexes = list(_cached_index_dict.values())
    print("Index Page: " + str(_cached_index_page))
    print("Total Pages: " + str(total_pages))
    if len(addresses) <= 10:
        reply = text.txt_bingo +  construct_indexes_list(_cached_city, addresses, indexes)
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply, parse_mode=ParseMode.HTML)
    else:
        addresses = addresses[0:10]
        indexes = indexes[0:10]
        reply = construct_indexes_list(_cached_city, addresses, indexes)


        reply_markup = construct_markup_index_list(_cached_index_page, total_pages)

        context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_bingo)
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                 parse_mode=ParseMode.HTML, reply_markup=reply_markup)

# "/help" handler
# Is a requirement of Telegram API
def help_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_help,
                             parse_mode=ParseMode.HTML)


# "/find_city <user input>" handler
def find_city_command(update, context):
    cities = mongo_receive_cities()
    try:
        if not context.args:
            context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_no_input,
                                     parse_mode=ParseMode.HTML)

        else:
            _input = ''
            for word in context.args:
                _input += word
            reply_list = []
            for city in cities:
                if _input.upper() in city.upper():
                    reply_list.append(city)
            if not reply_list:
                context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_no_reply,
                                         parse_mode=ParseMode.HTML)
            else:
                keyboard_reply = InlineKeyboardMarkup(construct_cities_list(reply_list, 1))
                context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_cities_received,
                                         reply_markup=keyboard_reply)
    except TypeError:
            context.bot.send_message(chat_id=update.effective_chat.id, text=text.txt_error)


# Contains Command Handlers
def main():
    # Create updater
    updater = Updater(token=get_token(), use_context=True)
    dispatcher = updater.dispatcher
    # "/start" command
    start_handler = CommandHandler('start', start_command)
    dispatcher.add_handler(start_handler)
    # "/city" command
    choose_city_handler = CommandHandler('city', city_command)
    dispatcher.add_handler(choose_city_handler)
    # Here we receive the response from the inline query
    dispatcher.add_handler(CallbackQueryHandler(inline_query_handler))
    # "/help" command
    dispatcher.add_handler(CommandHandler('help', help_command))
    # How we handle each other text received
    text_handler = MessageHandler(Filters.text & (~Filters.command), index_command)
    dispatcher.add_handler(text_handler)
    # "/find_city" command
    dispatcher.add_handler(CommandHandler('find_city', find_city_command))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
