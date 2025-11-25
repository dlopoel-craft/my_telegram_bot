import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os
import json
import datetime
import random
from pathlib import Path

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден в файле .env")

# Путь к файлу участников
PARTICIPANTS_FILE = Path("participants.json")

# Загружаем список участников при запуске
def load_participants():
    if PARTICIPANTS_FILE.exists():
        with open(PARTICIPANTS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:  # Если файл не пустой
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return []  # Если ошибка — возвращаем пустой список
    return []
    
# Сохраняем участника по username (если username нет — по first_name, но это менее надёжно)
def save_participant(user_data):
    participants = load_participants()
    user_id = user_data.get("user_id")
    if user_id is None:
        return

    for i, p in enumerate(participants):
        if p.get("user_id") == user_id:
            # Обновляем только указанные поля, остальное сохраняем
            p.update(user_data)
            participants[i] = p
            break
    else:
        participants.append(user_data)

    with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

async def send_media_and_message(message_obj, user_data):
    """Отправляет стикер/GIF/аудио и сообщение из user_data"""
    # Аудио
    if "audio" in user_data and user_data["audio"]:
        try:
            await message_obj.answer_audio(audio=user_data["audio"], caption="🎵 Включи меня!")
            await asyncio.sleep(2)
        except Exception:
            pass
    elif "audio_file_id" in user_data and user_data["audio_file_id"]:
        try:
            await message_obj.answer_audio(audio=user_data["audio_file_id"], caption="🎵 Включи меня!")
            await asyncio.sleep(2)
        except Exception:
            pass

    # Стикер
    if "sticker" in user_data and user_data["sticker"]:
        try:
            await message_obj.answer_sticker(sticker=user_data["sticker"])
            await asyncio.sleep(1)
        except Exception:
            pass

    # GIF
    if "gif" in user_data and user_data["gif"]:
        try:
            await message_obj.answer_animation(animation=user_data["gif"])
            await asyncio.sleep(1)
        except Exception:
            pass

    # Сообщение
    await message_obj.answer(user_data["message"])
    
# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик добавления .mp3
@dp.message(lambda m: m.audio)
async def get_audio_id(message: types.Message):
    print("MP3 file_id:", message.audio.file_id)
    
# Для получения file_id стикера
@dp.message(lambda m: m.sticker)
async def get_sticker_id(message: types.Message):
    print("Sticker file_id:", message.sticker.file_id)

# Для получения file_id GIF
@dp.message(lambda m: m.animation)
async def get_gif_id(message: types.Message):
    print("GIF file_id:", message.animation.file_id)
    
# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    # Создаём INLINE-кнопку
    keyboard = [
        [types.InlineKeyboardButton(text="🎁 Подумать о подарке", callback_data="gift_button")],
        [types.InlineKeyboardButton(text="🕒 Место и время", callback_data="time_info")],
        [types.InlineKeyboardButton(text="ℹ️ Информация", callback_data="bot_info")]
    ]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        "Привет! Я помогу тебе подготовиться к празднику для старичка 🎉\n\n"
        "Выбери, что тебя интересует:",
        reply_markup=reply_markup
    )

# Inline-кнопка "Место и время"
@dp.callback_query(lambda call: call.data == "time_info")
async def handle_time_info(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.answer()

    # Загружаем данные пользователя
    participants = load_participants()
    user_data = next((p for p in participants if p.get("user_id") == user_id), None)

    # Если есть старое сообщение — удаляем
    if user_data and "time_info_msg_id" in user_data:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_data["time_info_msg_id"])
        except Exception:
            pass  # Игнорируем ошибку, если сообщение уже удалено

    # Отправляем новое сообщение
    address = "г. Рязань, ул. Пугачева, д. 10, кв. 18"
    time = "6 декабря 2025 года в 19:00"
    map_link = "https://yandex.ru/maps/-/CLS15OOK"

    keyboard = [[types.InlineKeyboardButton(text="📍 Показать на карте", url=map_link)]]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    text = f"📍 **Место**: {address}\n🕗 **Время**: {time}"
    sent_msg = await call.message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)

    # Сохраняем message_id
    if user_data is None:
        user_data = {"user_id": user_id}
    user_data["time_info_msg_id"] = sent_msg.message_id
    save_participant(user_data)

# Inline-кнопка "Информация"
@dp.callback_query(lambda call: call.data == "bot_info")
async def handle_bot_info(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.answer()

    participants = load_participants()
    user_data = next((p for p in participants if p.get("user_id") == user_id), None)

    # Удаляем старое сообщение
    if user_data and "bot_info_msg_id" in user_data:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_data["bot_info_msg_id"])
        except Exception:
            pass

    # Отправляем новое
    text = (
        "Бот-помощник в организации туц-туц у Егорки 6 декабря 2025 года. ✅\n\n"
        "Что вам потребуется на данном мероприятии 👇\n"
        "🟢 Хорошо выспаться перед этим\n"
        "🟢 Зарядиться отличным настроением\n"
        "🟡 Машину лучше оставить дома🍺🍻\n"
        "🙏 У кого есть небольшие складные стулья, возьмите пожалуйста с собой🫶\n\n\n"
        "oldmanbirthday_bot v.1.0.1\n"
        "Для связи с создателем: @qdlopoelp"
    )
    sent_msg = await call.message.answer(text)

    # Сохраняем message_id
    if user_data is None:
        user_data = {"user_id": user_id}
    user_data["bot_info_msg_id"] = sent_msg.message_id
    save_participant(user_data)

# Команда /time
#@dp.message(Command("time"))
#async def cmd_time(message: types.Message):
#    await send_time_info(message)

# Команда /info
#@dp.message(Command("info"))
#async def cmd_info(message: types.Message):
#    await send_bot_info(message)
    
    # База по user_id:
SPECIAL_USERS_BY_ID = {
    "518928394": {
        "message": "Я покопался в мыслях у Егорки, и они таковы...\n Он будет очень сильно рад видеть вас с Саней на своем туц-туц, сильно вас ждет,\n и вообще вы красавцы!❤️\n P.S. Если сможете, возьмите стул(стулья)\n",
        "sticker": "CAACAgIAAxkBAAIClGkjlxThozzwRkYEh-jCZjEBVQjjAAKoAANXTxUINnLvCwfl94k2BA",
        "audio": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    },
    "1606619739": {
        "message": "Анастасия Игоревна, добрейшего вам времени суток!\n Это я сейчас залез в мысли к Егору🤔\n Странно, почему он с тобой на вы... Ну да ладно, возвращаемся к подарку...\n Его заветное желание, чтобы вы пришли на его праздник и от души повеселились, это все, что он хочет🥳\n",
        "sticker": "CAACAgIAAxkBAAIBFmki36Ce5yk3UR-OKI_NbDrByuTiAAIsAQAC9wLID6abwCn6K4ldNgQ",
        "audio": "CQACAgIAAxkBAAICfmkjhxfmjEeXoNTIHYKc5EJW2TqtAALmlwACLd0YSTkUVZ9eoCEKNgQ"
    },
    "1204015793": {
        "message": "Я подключился к мыслям старого, все проанализировал\n и в отношении вас, Сергей, там особая цель:\n Вам надо почему-то тусить за двоих🤔, это самое главное желание именинника🥳",
        "sticker": "CAACAgIAAxkBAAIBE2ki32fa1zZsz_DJGDQhV6BJLQbCAAKzCwACKlBRSiyjtgnsadPWNgQ",
        "audio": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    },
    "1350663194": {
        "message": "Аня, покопавшись в мыслях Егорки, он очень сильно ждет вас с Миханом,\n это его заветное желание, так что надо натуситься от души😊\n\n P.S. Мясца поесть...😋\n",
        "sticker": "CAACAgIAAxkBAAIClWkjl-sr1Sx3gz4K47KQaxNmwYp1AAKrAANXTxUI40m-ezFiQsk2BA",
        "audio": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    }
}
# Индивидуальные данные для особых пользователей
SPECIAL_USERS = {
    "wa_what": {
        "message": "Ася, я преместился в мысли именинника, вот что нашел у него в голове:\n Он очень соскучился и желает, чтобы ты схватила за руку Диму и вы в отличном настроении приехали к нему на праздник.\n P.S. у меня нет возможности подключаться к мыслям других людей, но что-то мне подсказывает, что по вам все очень соскучились 🥰",
        "sticker": "CAACAgIAAxkBAAIBF2ki4A-ahIdjkcmLttZW96J5Z-llAALTRgACH0tZSNhPyifcQcRnNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAICfmkjhxfmjEeXoNTIHYKc5EJW2TqtAALmlwACLd0YSTkUVZ9eoCEKNgQ"
    },
    "Laisteer": {
        "message": "Братааааааааан!\n Вот такие мысли были у именинника, когда я залез к нему в мысли 💡.\n Ну он думает, что ты и так все знаешь, Аню подмышку хватаешь и приезжаете тусить 🥳",
        "sticker": "CgACAgQAAxkBAAIBGWki4FMy-SkzI2bWpgqZRmXGtdFoAAJ_BAACKjTNUv8rzrUQbw7rNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAPUaSIxQ59X2NkfYnIsjP5hNoErW7kAAhaRAAIt3RBJwGOBwOC_tcE2BA" #WAZZZZZZZUP
    },
    "suffocatesand": {
        "message": "СААААААААНЯ!\n Я залез к имениннику в голову и это первая его мысль 😁.\n Он думает тебе ничего не надо говорить, ты и так все знаешь, от души душевно в душу приезжайте с Женькой и тусите до утра. \n\n P.S. Можно взять с собой настойку и (или) стулья, если смогете 😉",
        "gif": "CgACAgQAAxkBAAIBXWki-Z0-oOGCKnMqL4hzweCZlsVTAALxBgACziclU7qQ2z66TCvFNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE" #Сидр
    },
    "tamonikova": {
        "message": "Ритулькаааааааа!\n Это я залез в мысли к имениннику и это было в его голове 😁.\n К тебе у него есть важное пожелание, сейчас попробую перевести: тыц-тыц, дрыц-тыц, да-бум-тссс.\n Понимать бы еще что это значит...🤔\n Наверное он хочет, чтобы ты тусила от души 🤠 ",
        "sticker": "CAACAgIAAxkBAAIBGGki4Dc_p6rNax7w9awr0MHtXxk4AALRJQACN3uwSmqrpV8zXhDiNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAICe2kjhnaWtnum5X4eKivlQpGZOovjAALglwACLd0YSVpEkBc7Wp-UNgQ"
    },
    "myfaceistired": {
        "message": "Сейчас я подключусь к мыслям Егорки...\n Димка!\n Ты ответил, что пока не уверен, что сможешь прийти, поэтому самое его заветное желание, чтобы ты оказался на его празднике.\n P.S. Желательно без машины 😉",
        "sticker": "CAACAgIAAxkBAAIBFGki33a60fGGCERqr4u_41ZVr3ILAAIuAQAC9wLIDz2WPqTCJacaNgQ",  # замени на реальный file_id
        "audio_file_id": "Звук ID"
    },
    "UstyukovDmitry": {
        "message": "УУУУУУУУУУУУУУУУ!!!!!! СТАР-МЛАД БРАТ!\n Странно, конечно, что именно это было в мыслях у именинника, когда я к нему подключился🤔\n Но я думаю ты знаешь, что с этим надо делать😂\n",
        "sticker": "CgACAgQAAxkBAAICjmkjjOocls-BsN8WK8mXGvCdOyyqAALsBAACORStUsjZrX5vPEONNgQ",  # замени на реальный file_id
        "audio_file_id": "Звук ID"
    },
    "Magmelle": {
        "message": "Кааааатьм!\n Это я залез в голову к старому, а там это🤔\n Я думаю его заветное желание, чтобы вы с Диманом приехали на его праздник😄\n",
        "gif": "CgACAgQAAxkBAAICjGkji8YuFAymc_ajIBLOOd8op4XZAAKhBgACsAm1Uj5liQt684BHNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    },
    "qMashkap": {
        "message": "Мария!\n Я прочитал мысли Егорки, он будет очень рад видеть вас на своем празднике,\n и надеется, что у вас обоих на следующий день будет выходной и вы машину оставите у дома😉\n",
        "gif": "CgACAgQAAxkBAAICkWkjksoO8O0v7VqT264TohF-rAOGAAJBAwACMVAFU7H7QBzlE0qDNgQ",
        "audio_file_id": "CQACAgIAAxkBAAICe2kjhnaWtnum5X4eKivlQpGZOovjAALglwACLd0YSVpEkBc7Wp-UNgQ"
    },
    "k_frfr": {
        "message": "Залез я в мысли к старому...\n Он говорит:\n Ксю, просто приезжай потусить от души душевно в душу, ничего больше не надо😄\n",
        "gif": "CgACAgQAAxkBAAICk2kjk76Vahxdb8vAbYjvGHrh14DgAAIFAwACHwKFUw0JzYGGqH1QNgQ",
        "audio_file_id": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    },
	"just_katy_15": {
        "message": "Катя!\n Загружаю мысли Егора...\n Его заветное желание, чтобы вы с Андреем пришли к нему на праздник, но если он работает, придется тусить за двоих😁\n",
        "gif": "CgACAgQAAxkBAAICj2kjkGZ5MmVhPvEsgpJQHel0S7IRAAK_BQAC0eGlU5GxKYas4VaPNgQ",
        "audio_file_id": ""
    },
    "yuliatikhomirova": {
        "message": "Я залез в мысли Егорки и там:\n Юлькаааааа!😄\n Его самое заветное желание, если ты придешь на его праздник, я думаю он будет рад больше всего, больше ему ничего не надо 😉\n",
        "sticker": "CAACAgIAAxkBAAIBFmki36Ce5yk3UR-OKI_NbDrByuTiAAIsAQAC9wLID6abwCn6K4ldNgQ",  # замени на реальный file_id
        "audio_file_id": "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
    }
}

# Обработчик нажатия на inline-кнопку "🎁 Подумать о подарке"
import random

@dp.callback_query(lambda call: call.data == "gift_button")
async def handle_gift_button(call: types.CallbackQuery):
    user_id = call.from_user.id
    username = call.from_user.username
    first_name = call.from_user.first_name

    # Загружаем данные пользователя
    participants = load_participants()
    user_data = next((p for p in participants if p.get("user_id") == user_id), None)

    # Если подарок уже запрашивали — отправляем короткий ответ
    if user_data and user_data.get("gift_requested"):
        short_messages = [
            "Перегрелся... 🔥",
            "Я устал... 😴",
            "Лучший вариант для подарка я уже выдал... 🎁",
            "Микросхемы в отпуске... ⚙️"
        ]
        await call.message.answer(random.choice(short_messages))
        await call.answer()
        return

    # Иначе — показываем полную анимацию
    await call.answer()
    await call.message.answer("🧠 Прогреваю микросхемы...")
    await asyncio.sleep(2)
    await call.message.answer("🔍 Подключаю аналитические сервисы...")
    await asyncio.sleep(2)
    await call.message.answer("🕯️ Думаю о имениннике...")
    await asyncio.sleep(2)
    await call.message.answer("🎁 Анализирую, что он хочет больше всего...")
    await asyncio.sleep(2)
    await call.message.answer("✅ Всё готово, выдаю лучший вариант для подарка")
    await asyncio.sleep(2)

    # Отправляем персональный подарок
    sent = False
    if username and username in SPECIAL_USERS:
        data = SPECIAL_USERS[username]
        await send_media_and_message(call.message, data)
        sent = True
    elif str(user_id) in SPECIAL_USERS_BY_ID:
        data = SPECIAL_USERS_BY_ID[str(user_id)]
        await send_media_and_message(call.message, data)
        sent = True

    if not sent:
        COMMON_AUDIO_ID = "CQACAgIAAxkBAAICgGkjh0KsyEi4AAG292Hi8vAqY_HbnAAC6JcAAi3dGEmwA0s4DmlLwjYE"
        COMMON_STICKER_ID = "CAACAgIAAxkBAAIBGGki4Dc_p6rNax7w9awr0MHtXxk4AALRJQACN3uwSmqrpV8zXhDiNgQ"

        if COMMON_AUDIO_ID:
            try:
                await call.message.answer_audio(audio=COMMON_AUDIO_ID, caption="🎵 Включи меня")
                await asyncio.sleep(2)
            except Exception:
                pass
        if COMMON_STICKER_ID:
            try:
                await call.message.answer_sticker(sticker=COMMON_STICKER_ID)
                await asyncio.sleep(1)
            except Exception:
                pass

        greeting = f"@{username}, Я думаю, что самое важное желание именинника, что именно ты придешь на его праздник! 😉" if username else f"{first_name}, Я думаю, что самое важное желание именинника, что именно ты придешь на его праздник! 😉"
        await call.message.answer(greeting)

    # Сохраняем участника с флагом
    participant_data = {
        "user_id": user_id,
        "username": username or "Не указан",
        "first_name": first_name,
        "status": "no_response",
        "date": "2025-12-06T19:00:00",
        "address": "г. Рязань, ул. Пугачева, д. 10, кв. 18",
        "gift_requested": True  # ← ключевая строка
    }
    save_participant(participant_data)

    # Кнопки подтверждения
    keyboard = [
        [types.InlineKeyboardButton(text="🎉 Я приду!", callback_data="will_come"),
         types.InlineKeyboardButton(text="😔 Я не приду", callback_data="will_not_come")]
    ]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await call.message.answer("Ты придёшь на праздник?", reply_markup=reply_markup)

# Обработчик кнопки "Я приду"
@dp.callback_query(lambda call: call.data == "will_come")
async def handle_will_come(call: types.CallbackQuery):
    username = call.from_user.username
    first_name = call.from_user.first_name or "Друг"  # ← добавлено

    user_data = {
        "user_id": call.from_user.id,
        "username": username or "Не указан",
        "first_name": first_name,  # ← обязательно!
        "status": "confirmed",
        "date": "2025-12-06T19:00:00",
        "address": "г. Рязань, ул. Пугачева, д. 10, кв. 18"
    }
    save_participant(user_data)

    # Отправляем стикер отдельно
    await call.message.answer_sticker(sticker="CAACAgIAAxkBAAIBE2ki32fa1zZsz_DJGDQhV6BJLQbCAAKzCwACKlBRSiyjtgnsadPWNgQ")
    await call.message.answer(f"{first_name}, ты подтвердил участие в празднике! 🎉")

    # Обновляем кнопки в текущем сообщении
    keyboard = [[types.InlineKeyboardButton(text="🔄 Изменить ответ", callback_data="change_decision")]]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await call.message.edit_reply_markup(reply_markup=reply_markup)
    await call.answer()


@dp.callback_query(lambda call: call.data == "will_not_come")
async def handle_will_not_come(call: types.CallbackQuery):
    username = call.from_user.username
    first_name = call.from_user.first_name or "Друг"  # ← добавлено

    user_data = {
        "user_id": call.from_user.id,  # ← обязательно!
        "username": username or "Не указан",
        "first_name": first_name,
        "status": "no_response",
        "date": "2025-12-06T19:00:00",
        "address": "г. Рязань, ул. Пугачева, д. 10, кв. 18"
    }
    save_participant(user_data)

    await call.message.answer_sticker(sticker="CAACAgIAAxkBAAIBFWki34lp3tGyZ-eZ06mFrw95ptXbAAInAQAC9wLID-9HhEodcwYsNgQ")
    await call.message.answer(f"{first_name}, очень жаль, что ты не сможешь прийти 😔")

    keyboard = [[types.InlineKeyboardButton(text="🔄 Изменить ответ", callback_data="change_decision")]]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await call.message.edit_reply_markup(reply_markup=reply_markup)
    await call.answer()


@dp.callback_query(lambda call: call.data == "change_decision")
async def handle_change_decision(call: types.CallbackQuery):
    username = call.from_user.username
    first_name = call.from_user.first_name or "Друг"  # ← добавлено

    user_data = {
        "user_id": call.from_user.id,  # ← обязательно!
        "username": username or "Не указан",
        "first_name": first_name,
        "status": "no_response",
        "date": "2025-12-06T19:00:00",
        "address": "г. Рязань, ул. Пугачева, д. 10, кв. 18"
    }
    save_participant(user_data)

    await call.message.answer("Хорошо, давай еще подумаем!")

    # Обновляем кнопки на выбор
    keyboard = [
        [types.InlineKeyboardButton(text="🎉 Я приду!", callback_data="will_come"),
         types.InlineKeyboardButton(text="😔 Я не приду", callback_data="will_not_come")]
    ]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await call.message.edit_reply_markup(reply_markup=reply_markup)
    await call.answer()

@dp.message(Command("reset"))
async def reset_gifts(message: types.Message):
    if message.from_user.id != 1353926244:  # 🔐 ТВОЙ ID
        await message.answer("Команда доступна только владельцу.")
        return

    try:
        participants = load_participants()
        for p in participants:
            p["gift_requested"] = False  # сбрасываем у всех
        with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
            json.dump(participants, f, ensure_ascii=False, indent=2)
        await message.answer("✅ Все флаги подарков сброшены!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
@dp.message(Command("list"))
async def list_participants(message: types.Message):
    if message.from_user.id != 1353926244:
        await message.answer("Эта команда доступна только владельцу бота.")
        return

    participants = load_participants()
    if not participants:
        await message.answer("Пока никто не откликнулся 😢")
        return

    text = "✅ Участники праздника:\n\n"
    for p in participants:
        first_name = p.get("first_name", "Неизвестно")  # ← get() вместо []
        username = p.get("username", "Не указан")
        status = p.get("status", "no_response")
        if status == "confirmed":
            status_text = "✅"
        elif status == "declined":
            status_text = "❌"
        else:
            status_text = "❓"
        if username != "Не указан":
            text += f"• {status_text} {first_name} (@{username})\n"
        else:
            text += f"• {status_text} {first_name}\n"

    await message.answer(text)
    
async def send_time_info(message: types.Message):
    address = "г. Рязань, ул. Пугачева, д. 10, кв. 18"
    time = "6 декабря 2025 года в 19:00"
    map_link = "https://yandex.ru/maps/-/CLS15OOK"

    keyboard = [[types.InlineKeyboardButton(text="📍 Показать на карте", url=map_link)]]
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    text = f"📍 **Место**: {address}\n🕗 **Время**: {time}"
    await message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)
    
async def send_bot_info(message: types.Message):
    text = (
        "Бот-помощник в организации туц-туц у Егорки 6 декабря 2025 года. ✅\n\n"
        "Что вам потребуется на данном мероприятии 👇\n"
        "🟢 Хорошо выспаться перед этим\n"
        "🟢 Зарядиться отличным настроением\n"
        "🟡 Машину лучше оставить дома🍺🍻\n"
        "🙏 У кого есть небольшие складные стулья, возьмите пожалуйста с собой🫶\n\n\n"
        "oldmanbirthday_bot v.1.0.1\n"
        "Для связи с создателем: @qdlopoelp"
    )
    await message.answer(text)

async def send_reminder_to_eligible():
    """Отправляет напоминание только тем, кто придет или не ответил"""
    participants = load_participants()
    sent_count = 0

    for p in participants:
        user_id = p.get("user_id")
        status = p.get("status", "no_response")
        
        # Пропускаем тех, кто отказался
        if status == "declined" or not user_id:
            continue

        try:
            first_name = p.get("first_name", "друг")
            username = p.get("username")
            name = f"@{username}" if username and username != "Не указан" else first_name

            text = (
                f"🔔 {name}, доброе утро!\n\n"
                "💡 Напоминаю: завтра туц-туц у старичка! 🎉\n"
                "📅 6 декабря 2025 года\n"
                "🕗 19:00\n"
                "📍 г. Рязань, ул. Пугачева, д. 10, кв. 18\n\n"
                "❗ Не забудь:\n"
                "• Хорошенько выспаться\n"
                "• Взять с собой отличное настроение\n"
            )
            await bot.send_message(user_id, text)
            sent_count += 1
        except Exception as e:
            pass

    print(f"Напоминание отправлено {sent_count} пользователям.")

async def check_and_send_reminder():
    REMINDER_FLAG_FILE = Path("reminder_sent.flag")
    reminder_time = datetime.datetime(2025, 12, 5, 12, 0, 0)

    while True:
        try:
            now = datetime.datetime.now()
            if now >= reminder_time and not REMINDER_FLAG_FILE.exists():
                print("Отправляю напоминания...")
                await send_reminder_to_eligible()
                with open(REMINDER_FLAG_FILE, "w") as f:
                    f.write("sent")
                print("Напоминания отправлены.")
                break
        except Exception as e:
            print(f"Ошибка в фоновой задаче: {e}")
        await asyncio.sleep(60)
        
# Запуск бота
async def main():
    # Запускаем фоновую задачу для напоминания
    asyncio.create_task(check_and_send_reminder())
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())


