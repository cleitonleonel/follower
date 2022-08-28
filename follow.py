import os
import re
import sys
import time
import json
import asyncio
import warnings
import configparser
from dateutil import tz
from threading import Thread
from core.api import BlazeAPI
from utils.helpers import report_save
from datetime import datetime, timedelta, date
from telethon import types
from telethon.sync import TelegramClient, events
from telethon.tl.functions.messages import GetStickerSetRequest

__author__ = "Cleiton Leonel Creton"
__version__ = "0.0.1"

__message__ = f"""
Use com moderação, pois gerenciamento é tudo!
suporte: cleiton.leonel@gmail.com ou +55 (27) 9 9577-2291
"""

RLS_DATE = date(2023, 5, 1)
if date.today() - RLS_DATE >= timedelta(days=1):
    print("LICENÇA EXPIRADA ENTRE EM CONTATO COM \n"
          "O AUTOR DESSE PROJETO PARA ADQUIRIR \n"
          "A VERSÃO VITALÍCIA DO SISTEMA \n"
          "\n"
          ">>> cleiton.leonel@gmail.com <<<")
    sys.exit(0)

# config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
config = configparser.ConfigParser()
config.read('settings/config.ini', encoding="utf-8")

api_id = config.getint("bot", "api_id")
api_hash = config.get("bot", "api_hash")
session_name = config.get("bot", "session_name")

channel_id = config.getint("channels", "double_channel_id")

user = config.get("authentication", "user")
password = config.get("authentication", "password")

analizer_last_messages = config.getint("advanced", "analizer_last_messages")
red_pattern = config.get("advanced", "red_pattern")
black_pattern = config.get("advanced", "black_pattern")
after_pattern = config.get("advanced", "after_pattern")
win_word = config.get("advanced", "win_word")
loss_word = config.get("advanced", "loss_word")
enter_after_word = config.get("advanced", "enter_after_word")
number_enter_after_word = config.getint("advanced", "number_enter_after_word")
stop_after_word = config.get("advanced", "stop_after_word")
number_stop_after_word = config.getint("advanced", "number_stop_after_word")
filters_by_advanced_control = config.getboolean("advanced", "filters_by_advanced_control")
analizer_by_last_messages = config.getboolean("advanced", "analizer_by_last_messages")

protection_multiplier = config.getfloat("bets", "protection_multiplier")
protection_amount = config.getfloat("bets", "protection_amount")
protection_hand = config.getboolean("bets", "protection_hand")
protection_color = config.get("bets", "protection_color")
default_multiplier = config.getfloat("bets", "default_multiplier")
report_type = config.get("bets", "report_type")
tax_asserts = config.getint("bets", "tax_asserts")
martingale = config.getint("bets", "martingale")
stop_gain = config.getint("bets", "stop_gain")
stop_loss = config.getint("bets", "stop_loss")
amount = config.getfloat("bets", "amount")
is_demo = config.getboolean("bets", "is_demo")

art_effect = f"""
███████╗ ██████╗ ██╗     ██╗      ██████╗ ██╗    ██╗███████╗██████╗ 
██╔════╝██╔═══██╗██║     ██║     ██╔═══██╗██║    ██║██╔════╝██╔══██╗
█████╗  ██║   ██║██║     ██║     ██║   ██║██║ █╗ ██║█████╗  ██████╔╝
██╔══╝  ██║   ██║██║     ██║     ██║   ██║██║███╗██║██╔══╝  ██╔══██╗
██║     ╚██████╔╝███████╗███████╗╚██████╔╝╚███╔███╔╝███████╗██║  ██║
╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝

        author: {__author__} versão: {__version__}
        {__message__}
"""

print(art_effect)

client = TelegramClient(session_name, api_id, api_hash)
client.start()

ba = BlazeAPI(user, password)

first_balance = round(float(ba.get_balance()[0].get("balance")), 2) if not is_demo else round(float(10000))
current_balance = first_balance
print("SALDO INICIAL: ", first_balance)

last_doubles = []


def config_reload():
    config.read('settings/config.ini', encoding="utf-8")
    print(config.getint("bets", "tax_asserts"))


def refresh_display():
    os.system('cls' if os.name == 'nt' else 'export TERM=xterm && clear > /dev/null')


def get_timer():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def awaiting_status(status):
    while True:
        if ba.get_status() == status:
            return True
        time.sleep(0.1)


def get_doubles():
    doubles = ba.get_last_doubles()
    if doubles:
        return [[item["value"], item["color"]] for item in doubles["items"]][::-1]
    return []


def roulette_preview():
    global last_doubles
    last_doubles = last_doubles[1:]
    colored_string = ', '.join([
        f"\033[10;40m {item[0]} \033[m" if item[1] == "preto"
        else f"\033[10;41m {item[0]} \033[m" if item[1] == "vermelho"
        else f"\033[10;47m {item[0]} \033[m" for item in last_doubles])
    print(f"\r>>> {colored_string}\r", end="")


def parse_messages(message):
    color = None
    number = None

    before_number = re.findall(fr"{after_pattern}", message)
    if before_number:
        number = int(before_number[0])
    if re.findall(fr"{red_pattern}", message):
        color = "vermelho"
    elif re.findall(fr"{black_pattern}", message):
        color = "preto"
    return color, number


def get_color(number):
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, )


def calculate_martingale(enter, multiplier):
    return round(float(enter * multiplier), 2)


def calculate_profit(balance):
    return round(balance - first_balance, 2)


async def check_stop_win_or_loss(report_data):
    if profit >= abs(stop_gain):
        print("\rLIMITE DE GANHOS BATIDO, FECHANDO...\r")
        report_save(report_type, report_data, "stop_gain")
        ba.close_ws()
        await client.disconnect()
        print(f"\rPLACAR: {count_win} X {count_loss}", end="")
        sys.exit(0)

    elif count_loss >= stop_loss:
        print("\rLIMITE DE PERDAS BATIDO, FECHANDO...\r")
        report_save(report_type, report_data, "stop_loss")
        ba.close_ws()
        await client.disconnect()
        print(f"\rPLACAR: {count_win} X {count_loss}", end="")
        sys.exit(0)


async def wait_result(enter, bet):
    win = await ba.awaiting_double()

    result_dict = {
        "result": False,
    }

    roll_win = win["roll"]
    result_dict["roll"] = roll_win
    color_win = get_color(win["color"])
    result_dict["color"] = color_win

    if color_win == enter:
        result_dict["result"] = True
        result_dict["win"] = True
    else:
        result_dict["win"] = False

    bet["object"] = result_dict
    return result_dict


async def get_messages(limit=100):
    list_messages = []
    messages = await client.get_messages(channel_id, limit=limit)
    for message in messages:
        list_messages.append([message.sender_id, message.text])
    return list_messages


async def get_history(limit=100):
    list_messages = []
    async for message in client.iter_messages(channel_id, limit=limit):
        list_messages.append([message.sender_id, message.text])
    return list_messages


async def signs_health(limit=analizer_last_messages):
    global green_percent, red_percent
    try:
        history = await get_messages(limit)
        count_green = 0
        count_red = 0
        for message in history[:limit]:
            count_green += message[1].count(win_word)
            count_red += message[1].count(loss_word)
        total_history = count_green + count_red
        green_percent = (count_green * 100) / total_history
        red_percent = (count_red * 100) / total_history
    except:
        pass


async def assert_percent():
    while True:
        await signs_health()
        await asyncio.sleep(5)


async def double_bets(color, current_amount, current_protection_amount, balance):
    global result_bet
    global result_protection
    print("BALANCE ANTES DE APOSTAR: ", current_balance)
    result_bet = {}
    result_dict = {}
    result_protection = {}
    result_dict["object"] = {}
    print(f"\nAPOSTA DE {float(current_amount):.2f} R$ FEITA NO {color} às {get_timer()}\r")
    balance -= current_amount
    if not is_demo:
        ba.double_bets(color, current_amount)
    first_thread = Thread(target=asyncio.run, args=(wait_result(color, result_bet),))
    first_thread.start()
    if protection_hand:
        balance -= current_protection_amount
        print(f"\nPROTEÇÃO DE {float(current_protection_amount):.2f} R$ FEITA NO {protection_color} às {get_timer()}\r")
        time.sleep(2.5)
        if not is_demo:
            ba.double_bets(protection_color, current_protection_amount)
        protection_thread = Thread(target=asyncio.run, args=(wait_result(protection_color, result_protection),))
        protection_thread.start()
        while protection_thread.is_alive():
            time.sleep(0.1)
    while first_thread.is_alive():
        time.sleep(0.1)

    if result_protection.get("object"):
        print(f'\r{color}: {"GREEN" if result_bet["object"]["win"] else "LOSS"} | '
              f'{protection_color}: {"GREEN" if result_protection["object"]["win"] else "LOSS"} | '
              f'HORÁRIO: {get_timer()}\r')
        if result_bet["object"]["win"] or result_protection["object"]["win"]:
            result_dict["object"]["win"] = True
            if result_bet["object"]["win"]:
                balance += current_amount * 2
            elif result_protection["object"]["win"]:
                balance += current_protection_amount * 14
        else:
            result_dict["object"]["win"] = False
    else:
        print(f'\r{color}: {"GREEN" if result_bet["object"]["win"] else "LOSS"} | HORÁRIO: {get_timer()}\r')
        if result_bet["object"]["win"]:
            result_dict["object"]["win"] = True
            balance += current_amount * 2
        else:
            result_dict["object"]["win"] = False

    result_dict["object"]["balance"] = round(float(balance), 2)
    result_dict["object"]["profit"] = calculate_profit(round(float(balance), 2))
    result_dict["object"]["created"] = get_timer()

    return result_dict


@client.on(events.NewMessage(chats=[channel_id]))
async def my_event_handler(event):
    global count_win, count_loss, is_gale, profit, current_balance, count_number_after_word, \
        count_number_stop_after_word, count_martingale, green_percent, red_percent, report_data, last_doubles

    message = event.raw_text
    # print(f"\n{message}\n")
    local_datetime = event.date.astimezone(tz.tzlocal())

    if filters_by_advanced_control:
        count_number_after_word += max([1 if message.count(text) > 0 else 0
                                        for text in json.loads(enter_after_word)])
        count_number_stop_after_word += max([1 if message.count(text) > 0 else 0
                                             for text in json.loads(stop_after_word)])
        if count_number_after_word >= number_enter_after_word:
            if count_number_stop_after_word > 1:
                count_number_stop_after_word += 1
            elif count_number_stop_after_word >= number_stop_after_word + 1:
                count_number_after_word = 0
                count_number_stop_after_word = 0
                return
        else:
            return

    elif analizer_by_last_messages:
        if green_percent and green_percent < tax_asserts:
            print(f"\rTAXA DE ASSERTIVIDADE: {green_percent} %\r")
            print(f"\rASSERTIVIDADE MUITO BAIXA, AGUARDANDO RECUPERAÇÃO\r")
            return

    current_color, before_number = parse_messages(message)
    if before_number and awaiting_status("complete"):
        if "possível" in message:
            print(f"\rPOSSÍVEL ENTRADA, AGUARDANDO CONFIRMAÇÃO\r")
        last_doubles = get_doubles()[:-1]
        double = await ba.get_double()
        last_doubles.append([double["roll"], get_color(double["color"])])
        roulette_preview()
        data = await ba.get_double()
        if data["roll"] and data["roll"] != before_number:
            print("\rENTRADA CANCELADA\r")
            return
        print(f"\nENTRADA, CONFIRMADA ÀS {get_timer()}\n")
        print(f'\nENTRAR APÓS O NÚMERO {before_number} '
              f'COR {"preto" if before_number > 7 else "vermelho" if before_number <= 7 else "branco"}\r')
    current_protection_amount = float(protection_amount)
    current_amount = float(amount)
    if current_color:
        while True:
            if is_gale and count_martingale <= martingale:
                print(f"\rENTRANDO NO GALE {count_martingale}!!!\r")
            if awaiting_status("waiting"):
                print(f"\rTAXA DE ASSERTIVIDADE: {float(green_percent):.2f} %\r" if green_percent else "")
                if count_martingale <= martingale:
                    result_bets = await double_bets(current_color, current_amount,
                                                    current_protection_amount, current_balance)
                    current_balance = result_bets["object"]["balance"]
                    report_data.append(result_bets)
                    if not result_bets["object"]["win"]:
                        current_amount = calculate_martingale(current_amount, default_multiplier)
                        current_protection_amount = calculate_martingale(current_protection_amount,
                                                                         protection_multiplier)
                        count_martingale += 1
                        is_gale = True
                        profit = calculate_profit(current_balance)
                        print(f"\rLUCRO ATUAL: {profit}\r")
                        print(f"\rSALDO ATUAL: {current_balance}\r")
                    else:
                        print(f"\rWIN !!!")
                        count_win += 1
                        is_gale = False
                        count_martingale = 0
                        profit = calculate_profit(current_balance)
                        print(f"\rLUCRO ATUAL: {profit}\r")
                        print(f"\rSALDO ATUAL: {current_balance}\r")
                        await check_stop_win_or_loss(report_data)
                        break
                else:
                    print(f"\rLOSS !!!")
                    count_loss += 1
                    is_gale = False
                    count_martingale = 0
                    profit = calculate_profit(current_balance)
                    await check_stop_win_or_loss(report_data)
                    break

    print(f"\rPLACAR: {count_win} X {count_loss}", end="")


if __name__ == "__main__":
    is_gale = False
    profit = None
    count_win = 0
    count_loss = 0
    count_martingale = 0
    green_percent = None
    red_percent = None
    report_data = []
    result_bet = {}
    result_protection = {}
    count_number_after_word = 0
    count_number_stop_after_word = 0
    os.system('color 0f') if os.name == 'nt' else None
    warnings.filterwarnings("ignore")
    print("\rANALISANDO SINAIS, AGUARDANDO POSSIBILIDADE DE ENTRADA...\n")

with client:
    client.loop.create_task(assert_percent())
    try:
        client.run_until_disconnected()
    except:
        print("\rSAINDO...\r")
