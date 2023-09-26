from aiogram import Bot, Dispatcher, types, executor #импортировали aiogram
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
import requests
import xml.etree.ElementTree as ET
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

api_token = os.getenv('API_TOKEN')
api_key = os.getenv('MY_API_KEY')

bot = Bot(token=api_token)

storage = MemoryStorage()
db_path = './app_data/dbase.db'
my_api_key = api_key

dp = Dispatcher(bot, storage = storage)

class CheckСurrencyStates(StatesGroup):
    СurrencyID = State()
    DateTime = State()

class DiffCurrency(StatesGroup):
    СurrencyID = State()
    DateTime_1 = State()
    DateTime_2 = State()
    Number = State()

class CurToCur(StatesGroup):
    СurrencyID_1 = State()
    СurrencyID_2 = State() 

class User:
    def __init__(self, telegram_id) -> None:
        self.telegram_id = telegram_id

    def checkUserRecord(self):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)''')
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (self.telegram_id,))
        db_data = cursor.fetchone()
        if db_data is None:
            result = None
            conn.close()
        else:
            result = db_data[0]
            conn.close()
        return result
    
    def createUserRecord(self):
        insterted_id = None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)''')
        cursor.execute('INSERT INTO users (telegram_id) VALUES (?)', (self.telegram_id,))
        conn.commit()
        insterted_id = cursor.lastrowid
        conn.close()
        return insterted_id


def is_valid_date(date_str): #проверяем дату на валидность (не должна превосходить текущей, и не меньше 1992 года - данных на сате ЦБ нет)
    try:
        date = datetime.datetime.strptime(date_str, '%d/%m/%Y')
        if date <= datetime.datetime.now() and date >= datetime.datetime(1992, 1, 1):
            return True
    except ValueError:
        pass
    return False

def check_input_currency(cur): #проверяем введенную валюту, все что есть на сайте ЦБ
    if cur in ['AUD', 'AZN', 'GBP', 'AMD', 'BYN', 'BGN', 'BRL', 'HUF', 'VND',
                           'HKD', 'GEL', 'DKK', 'AED', 'USD', 'EUR', 'EGP', 'INR', 'IDR', 'KZT', 'CAD',
                           'QAR', 'KGS', 'CNY', 'MDL', 'NZD', 'NOK', 'PLN', 'RON', 'XDR', 'SGD', 'TJS', 'THB',
                           'TRY', 'TMT', 'UZS', 'UAH', 'CZK', 'SEK', 'CHF', 'RSD', 'ZAR', 'KRW', 'JPY']:
        return True
    else:
        return False

def checkCurrency(datetime, currency): #курс валюты на конкретную дату
    url = f'https://www.cbr.ru/scripts/XML_daily.asp'
    response = requests.get(url)
    if response.status_code == 200:
        usd_rate = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime}').text).find(
        f'./Valute[CharCode="{currency}"]/Value').text.replace(',', '.'))
        nomin = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime}').text).find(
        f'./Valute[CharCode="{currency}"]/Nominal').text.replace(',', '.'))
        return round(usd_rate/nomin, 2)
    else:
        return False

def differ(currency, number, datetime1, datetime2): #выигрыш/проигрыш от разности курсов валют
    url = f'https://www.cbr.ru/scripts/XML_daily.asp'
    response = requests.get(url)
    if response.status_code == 200:
        usd_rate_1 = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime1}').text).find(
        f'./Valute[CharCode="{currency}"]/Value').text.replace(',', '.'))
        usd_rate_2 = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime2}').text).find(
        f'./Valute[CharCode="{currency}"]/Value').text.replace(',', '.'))
        nomin1 = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime1}').text).find(
        f'./Valute[CharCode="{currency}"]/Nominal').text.replace(',', '.'))
        nomin2 = float(
        ET.fromstring(requests.get(f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime2}').text).find(
        f'./Valute[CharCode="{currency}"]/Nominal').text.replace(',', '.'))
        return round((usd_rate_2/nomin2 - usd_rate_1/nomin1)*number, 2)
    else:
        return False

def curTocur(currency1, currency2): #обменный курс для пары валют
    url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={currency1}&to_currency={currency2}&apikey={my_api_key}.json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("Realtime Currency Exchange Rate") != None:
            return round(float(data.get("Realtime Currency Exchange Rate", {})["5. Exchange Rate"]), 2)
        else:
            return None
    else:
        return False

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user = User(message.from_user.id)
    user_record = user.checkUserRecord()
    if user_record is None:
        user.createUserRecord() 
        await message.reply("Привет! Регистрация прошла успешно")
    else:
        await message.reply("Привет! Вы уже зарегистрированы")

@dp.message_handler(commands=['getCurrency']) 
async def getCurrency_start(message: types.Message):
    await message.reply("Введите дату (в формате dd/mm/yyyy) и код валюты. Например, 01/01/2020 usd") 
    await CheckСurrencyStates.СurrencyID.set() 

@dp.message_handler(state=CheckСurrencyStates.СurrencyID)
async def getCurrency_exec(message: types.Message, state: FSMContext): 
    params = message.text.upper().split()
    parameter1 = params[0]
    parameter2 = params[1]

    if check_input_currency(parameter2) == False:
        await message.reply("Не удалось найти валюту. Проверьте и возвращайтесь :)")
    else:
        if is_valid_date(parameter1):
            if checkCurrency(parameter1, parameter2):
                await message.reply("Цена " + str(parameter2) + " на сайте ЦБ равна " + str(checkCurrency(parameter1, parameter2)) + " на дату " + str(parameter1))
            else:
                await message.reply("Что-то пошло не так. Поробуйте позднее")
        else:
            await message.reply("Странная дата. Возможно, вы ошиблись")
    await state.finish()

@dp.message_handler(commands=['difCurr'])
async def diff_start(message: types.Message):
    await message.reply("Введите наименование валюты, сумму и даты (дату покупки и продажи в формате dd/mm/yyyy). Например, usd 100 01/01/2020 13/04/2023") 
    await DiffCurrency.СurrencyID.set()

@dp.message_handler(state=DiffCurrency.СurrencyID)
async def diff_exec(message: types.Message, state: FSMContext):
    params = message.text.upper().split()
    parameter1 = params[0]
    parameter2 = float(params[1])
    parameter3 = params[2]
    parameter4 = params[3]

    if check_input_currency(parameter1) == False:
        await message.reply("Не удалось найти валюту. Проверьте и возвращайтесь :)")
    else:
        if (is_valid_date(parameter3) == True and is_valid_date(parameter4) == True):
            date1 = datetime.datetime.strptime(parameter3, '%d/%m/%Y')
            date2 = datetime.datetime.strptime(parameter4, '%d/%m/%Y')
            if (date1 <= date2):
                cur = differ(parameter1, parameter2, parameter3, parameter4) 
                if cur:
                    if (cur < 0):
                        await message.reply("Разница составляет. " + str(cur) + " К сожалению, вы потеряли, а не выйграли с покупки валюты.")
                    if (cur >= 0):
                        await message.reply("Разница составляет. " + str(cur) + " Поздравляем, вы выйграли с покупки валюты.")
                else:
                    await message.reply("Что-то пошло не так. Поробуйте позднее")
            else:
               await message.reply("Дата покупки должна быть меньше даты продажи, а у вас не так, проверьте и вернитесь :)") 
        else:
            await message.reply("Что-то не так с датами. Возможно, вы ошиблись")
    await state.finish()

@dp.message_handler(commands=['curTocur'])
async def curTocur_start(message: types.Message):
    await message.reply("Введите две валюты. Например, USD EUR") 
    await CurToCur.СurrencyID_1.set()

@dp.message_handler(state=CurToCur.СurrencyID_1)
async def curTocur_exec(message: types.Message, state: FSMContext):
    params = message.text.split()
    parameter1 = params[0].upper()
    parameter2 = params[1].upper()

    cur = curTocur(parameter1, parameter2)
    if cur != False:
        if (cur == None):
            await message.reply("Что-то не так с валютами, возможно, таких не существует")
        else:
            await message.reply("Обменный курс в реальном времени для пары валют " + str(parameter1) + " и " + str(parameter2) + " равен " + str(cur))
    else:
        await message.reply("Что-то пошло не так. Поробуйте позднее")
    await state.finish()


if __name__ == '__main__':
        executor.start_polling(dp, skip_updates=True)


