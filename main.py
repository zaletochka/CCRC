import telebot
from telebot import types
import psycopg2
def make_connection():
    """Create connection for work with PostgreSQL"""
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="098",
        host="127.0.0.1",
        port="5432")

bot = telebot.TeleBot('7337471159:AAHKjiTqYJmTfkAHbUUPB5EiRrxjHoQ42Bs')

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = 'started'
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Континент', 'Страна', 'Регион', 'Поселение')
    bot.send_message(
        message.chat.id,
        'Привет! Этот бот предназначен для получения информации по континенту/стране/региону/населенному пункту. '
        'Выберите одну из команд ниже для продолжения.',
        reply_markup=markup
    )

@bot.message_handler(commands=['stop'])
def stop(message):
    user_state.pop(message.chat.id, None)
    bot.send_message(message.chat.id, 'Чат завершен. Для нового запроса введите /start.')

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'started')
def handle_choice(message):
    choice = message.text.lower()
    if choice == 'континент':
        bot.send_message(message.chat.id, 'Введите название континента:')
        user_state[message.chat.id] = 'continent'
        bot.register_next_step_handler(message, continent_choice)
    elif choice == 'страна':
        bot.send_message(message.chat.id, 'Введите название страны:')
        user_state[message.chat.id] = 'country'
        bot.register_next_step_handler(message, country_choice)
    elif choice == 'регион':
        bot.send_message(message.chat.id, 'Введите название региона:')
        user_state[message.chat.id] = 'region'
        bot.register_next_step_handler(message, region_choice)
    elif choice == 'поселение':
        bot.send_message(message.chat.id, 'Введите название населенного пункта:')
        user_state[message.chat.id] = 'city'
        bot.register_next_step_handler(message, city_choice)
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, выберите одну из команд ниже.')
        start(message)

def continent_choice(message):
    continent = message.text
    c = make_connection()
    cursor = c.cursor()
    cursor.execute("""select name from continent""")
    continents = [i[0].title() for i in cursor.fetchall()]
    if continent.title() in continents:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Количество стран', 'Сами страны')
        bot.send_message(message.chat.id, 'Что вы хотите узнать?', reply_markup=markup)
        user_state[message.chat.id] = {'step': 'continent_choice', 'continent': continent}
        bot.register_next_step_handler(message, continent_result)
    else:
        bot.send_message(message.chat.id, f'Такого континента {message.text} не существует. Попробуйте снова.')
        bot.register_next_step_handler(message, continent_choice)
    c.commit()
    c.close()

def continent_result(message):
    continent = user_state[message.chat.id]['continent']
    markup = types.ReplyKeyboardRemove()
    if message.text == 'Количество стран':
        c = make_connection()
        cursor = c.cursor()
        cursor.execute(f"""select count(*) from country where id_continent = (select id from continent where name='{continent}')""")
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'На континенте {continent} находится {count} стран.', reply_markup=markup)
        c.commit()
        c.close()
    elif message.text == 'Сами страны':
        c = make_connection()
        cursor = c.cursor()
        cursor.execute(f"""select name from country where id_continent = (select id from continent where name='{continent}')""")
        countries = [i[0] for i in cursor.fetchall()]
        bot.send_message(message.chat.id, f'На континенте {continent} находятся следующие страны: {", ".join(countries)}', reply_markup=markup)
        c.commit()
        c.close()
    else:
        bot.send_message(message.chat.id, 'Неверный выбор. Попробуйте снова.', reply_markup=markup)
        bot.register_next_step_handler(message, continent_result)
    prompt_restart(message)

def country_choice(message):
    country = message.text
    c = make_connection()
    cursor = c.cursor()
    cursor.execute("""select name from country""")
    countries = [i[0].title() for i in cursor.fetchall()]
    if country.title() in countries:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('На каком континенте', 'Количество регионов', 'Сами регионы')
        bot.send_message(message.chat.id, 'Что вы хотите узнать?', reply_markup=markup)
        user_state[message.chat.id] = {'step': 'country_choice', 'country': country}
        bot.register_next_step_handler(message, country_result)
    else:
        bot.send_message(message.chat.id, f'Такой страны {message.text} не существует. Попробуйте снова.')
        bot.register_next_step_handler(message, country_choice)
    c.commit()
    c.close()

def country_result(message):
    country = user_state[message.chat.id]['country']
    markup = types.ReplyKeyboardRemove()
    c = make_connection()
    cursor = c.cursor()
    if message.text == 'На каком континенте':
        cursor.execute(f"""select name from continent where id = (select id_continent from country where name='{country}')""")
        continent = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'Страна {country} находится на континенте {continent}.', reply_markup=markup)
    elif message.text == 'Количество регионов':
        cursor.execute(f"""select count(*) from region where country_id = (select id from country where name='{country}')""")
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'В стране {country} находится {count} регионов.', reply_markup=markup)
    elif message.text == 'Сами регионы':
        cursor.execute(f"""select name from region where country_id = (select id from country where name='{country}')""")
        regions = [i[0] for i in cursor.fetchall()]
        bot.send_message(message.chat.id, f'В стране {country} находятся следующие регионы: {", ".join(regions)}', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Неверный выбор. Попробуйте снова.', reply_markup=markup)
        bot.register_next_step_handler(message, country_result)
    c.commit()
    c.close()
    prompt_restart(message)

def region_choice(message):
    region = message.text
    c = make_connection()
    cursor = c.cursor()
    cursor.execute("""select name from region""")
    regions = [i[0].title() for i in cursor.fetchall()]
    if region.title() in regions:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('В какой стране', 'Количество населенных пунктов', 'Сами населенные пункты')
        bot.send_message(message.chat.id, 'Что вы хотите узнать?', reply_markup=markup)
        user_state[message.chat.id] = {'step': 'region_choice', 'region': region}
        bot.register_next_step_handler(message, region_result)
    else:
        bot.send_message(message.chat.id, f'Такого региона {message.text} не существует. Попробуйте снова.')
        bot.register_next_step_handler(message, region_choice)
    c.commit()
    c.close()

def region_result(message):
    region = user_state[message.chat.id]['region']
    markup = types.ReplyKeyboardRemove()
    c = make_connection()
    cursor = c.cursor()
    if message.text == 'В какой стране':
        cursor.execute(f"""select name from country where id = (select country_id from region where name='{region}')""")
        country = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'Регион {region} находится в стране {country}.', reply_markup=markup)
    elif message.text == 'Количество населенных пунктов':
        cursor.execute(f"""select count(*) from city where region_id = (select id from region where name='{region}')""")
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'В регионе {region} находится {count} населенных пунктов.', reply_markup=markup)
    elif message.text == 'Сами населенные пункты':
        cursor.execute(f"""select name from city where region_id = (select id from region where name='{region}')""")
        cities = [i[0] for i in cursor.fetchall()]
        bot.send_message(message.chat.id, f'В регионе {region} находятся следующие населенные пункты: {", ".join(cities)}', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Неверный выбор. Попробуйте снова.', reply_markup=markup)
        bot.register_next_step_handler(message, region_result)
    c.commit()
    c.close()
    prompt_restart(message)

def city_choice(message):
    city = message.text
    c = make_connection()
    cursor = c.cursor()
    cursor.execute("""select name from city""")
    cities = [i[0].title() for i in cursor.fetchall()]
    if city.title() in cities:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('В каком регионе')
        bot.send_message(message.chat.id, 'Что вы хотите узнать?', reply_markup=markup)
        user_state[message.chat.id] = {'step': 'city_choice', 'city': city}
        bot.register_next_step_handler(message, city_result)
    else:
        bot.send_message(message.chat.id, f'Такого населенного пункта {message.text} не существует. Попробуйте снова.')
        bot.register_next_step_handler(message, city_choice)
    c.commit()
    c.close()

def city_result(message):
    city = user_state[message.chat.id]['city']
    markup = types.ReplyKeyboardRemove()
    c = make_connection()
    cursor = c.cursor()
    if message.text == 'В каком регионе':
        cursor.execute(f"""select name from region where id = (select region_id from city where name='{city}')""")
        region = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f'Населенный пункт {city} находится в регионе {region}.', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Неверный выбор. Попробуйте снова.', reply_markup=markup)
        bot.register_next_step_handler(message, city_result)
    c.commit()
    c.close()
    prompt_restart(message)

def prompt_restart(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Континент', 'Страна', 'Регион', 'Поселение')
    bot.send_message(
        message.chat.id,
        'Выберите следующую команду или введите /stop для завершения чата.',
        reply_markup=markup
    )
    user_state[message.chat.id] = 'started'

bot.polling(none_stop=True)
