from aiogram import  Bot, Dispatcher, executor, types
import requests
import json
import config
from datetime import datetime
import bs4
import re

''' ссылка на апи погодного сайта
https://api.openweathermap.org/data/2.5/weather?q={city name}&appid={API key}&units=metric
'''
''' сайт и headers для веб-скрапинга
'''
full_url = 'https://azbyka.ru/days/'

HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36', 'Accept': '*/*'}
HEADERS1 = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate, br',
'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
'Connection': 'keep-alive',
'Cookie': 'hl=ru; fl=ru; _ga=GA1.2.204020777.1659128231; _ym_uid=16591282311005742073; _ym_d=1659128231; __gads=ID=706ffeaa414b90ea-22547adcdfcd00cf:T=1659128234:S=ALNI_MYUpMw_taANvQ9HrMTdS3B0hbvehg; habr_web_home_feed=/all/; _gid=GA1.2.1558690067.1662297810; _ym_isad=2',
'Host': 'habr.com',
'Sec-Fetch-Dest': 'document',
'Sec-Fetch-Mode': 'navigate',
'Sec-Fetch-Site': 'none',
'Sec-Fetch-User': '?1',
'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
            'Accept': '*/*' }

API_KEY = config.API_KEY
bot = Bot(config.BOT)
dp = Dispatcher(bot)

#основные кнопки бота
weather_bt = types.InlineKeyboardButton('Погода', callback_data='weather')
data_bt = types.KeyboardButton('Дата', callback_data='data')
orth_bt = types.KeyboardButton('Сегодняшний праздник', callback_data='orth')

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.row(data_bt, weather_bt)
    markup.row(orth_bt)
    await message.answer('Привет, я показываю погоду или православные праздники',  reply_markup=markup)

'''
    функция с действиями бота при нажатии на кнопки "Дата", "Погода", "Сегодняшний праздник"
'''
@dp.callback_query_handler(text=['data', 'weather', 'orth'])
async def callback(callback_query: types.CallbackQuery):
    if callback_query.data == 'data':
        date_and_time = datetime.now()
        dt_str = f'Точное время {date_and_time.hour}:{date_and_time.minute}\n' \
                     f'Дата {date_and_time.day}/{date_and_time.month}/{date_and_time.year}'
        await callback_query.message.answer(dt_str)
    elif callback_query.data == 'weather':
        await callback_query.message.answer('Введите название города')
    elif callback_query.data == 'orth':
        calender_str = show_calender()
        await callback_query.message.answer(calender_str)
        await callback_query.message.answer(f"Источник: {full_url}")
    else:
        await callback_query.message.answer('Ошибка')

''' 
    подключение к сайту погода с помощью апи,
    получение температуры и погодной иконки с последующей их выдачей 
'''
@dp.message_handler(content_types=['text'])
async def get_weather(message: types.Message):
    city = message.text.strip().lower()
    resp = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric')
    if resp.status_code == 200:
        data = json.loads(resp.text)
        temperature = data['main']['temp']
        icon = data['weather'][0]['icon']
        await message.answer_photo(f'https://openweathermap.org/img/wn/{icon}@2x.png')
        await message.reply(f'Температура воздуха: {temperature}')
    else:
        await message.reply(f'Город указан неверно')

''' 
    функция для веб-скрапинга страницы сайта с информацией о календаре,
    обработка полученных данных и представление в виде строки
'''
def show_calender():
    response = requests.get(full_url, headers=HEADERS)
    text = response.text
    soup = bs4.BeautifulSoup(text, features='html.parser')
    final_str = ''
    p_results = soup.find('div', {"class": "text day__text"}).select("p")
    shadow_results = soup.find('div', {"class": "shadow"})
    shadow_str = ''
    for s_result in shadow_results:
        text = s_result.get_text()
        if text:
            replaced_text = re.sub(r'(\n|\t|\xa0)*', '', text)
            shadow_str += f'{replaced_text}'

    for p_result in p_results:
        text = p_result.get_text()
        if text:
            replaced_text = re.sub(r'(\n|\t)*', '', text)
            final_str += f'{replaced_text}; '
    final_str = final_str.strip()
    final_str = final_str.strip(';')
    final_replaced = re.sub(r'; ', ';\n',final_str)

    return f'{shadow_str}\n{final_replaced}'

executor.start_polling(dp)
