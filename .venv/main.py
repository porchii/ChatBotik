import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramNotFound, TelegramForbiddenError, TelegramUnauthorizedError, TelegramBadRequest
from aiogram.utils.chat_member import ADMINS
from aiogram.types.message import ContentType
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from cfg import admins, TOKEN
from Backend import DataBase
from notifier import Scheduler

db = DataBase()


bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
notifier = Scheduler(bot_token=TOKEN, db=db)
rt = Router()

# FSM context groups
class Form(StatesGroup):
    branch = State()
    shift = State()
    add_shift = State()
    group_name = State()
    settings = State()
    table = State()
    global_msg = State()


async def is_admin(user_id, chat_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)

        return  isinstance(member, ADMINS)
    except:
        return False

@rt.message(Command("here"))
async def here_command(message: Message):
    is_admin_user = message.chat.type == 'private' or await is_admin(message.from_user.id,
                                                                                    message.chat.id)
    if not is_admin_user:
        return
    try:
        await message.answer("Теперь фото с расписанием будут отправляться сюда")
        await db.change_thread_value(message.chat.id, message.message_thread_id)
    except Exception as e:
        await bot.send_message(admins[0], f'Баба1 {e}')

@rt.message(F.text == 'Меню🏠')
async def home(message: Message, state: FSMContext):
    is_admin_user = message.chat.type == 'private' or await is_admin(message.from_user.id,
                                                                     message.chat.id)
    if not is_admin_user:
        return
    await state.clear()
    await bot.send_message(message.chat.id, "Доступные дейcтвия:\n\n"
                                                  "1. Филиал: Выбрать филиал\n\n"
                                                  "2. Смена: Выбрать смену обучения.\n\n"
                                                  "3. Класс: Выбрать класс обучения\n\n"
                                            "4. Получить расписание: Получить известное на данный момент расписание.",
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [
                                     InlineKeyboardButton(text='Филиал🏫', callback_data='get_branch')
                                 ],
                                 [
                                     InlineKeyboardButton(text='Смена⏰', callback_data='get_shift'),
                                     InlineKeyboardButton(text='Класс🗓', callback_data='get_group'),
                                 ],
                                 [
                                     InlineKeyboardButton(text='Получить расписание🎓', callback_data='schedule')
                                 ]
                             ]
                         ))

async def menu(message: Message, state: FSMContext):
    await state.clear()

@rt.message(F.text == 'Профиль🔑')
async def profile(message: Message, state: FSMContext):
    is_admin_user = message.chat.type == 'private' or await is_admin(message.from_user.id,
                                                                     message.chat.id)
    if not is_admin_user:
        return
    await state.clear()
    await message.answer("👇")
    data = await db.get_user_data(message.chat.id)
    chat = await bot.get_chat(message.chat.id)
    await message.answer(f"🔑Профиль\n"
                         f"├👤Ник + ID: {chat.first_name}({message.chat.id})\n"
                         f"├🏫Филиал: {data[3]}\n"
                         f"├⏰Смена: {data[2]}\n"
                         f"└🗓Класс: {data[1]}"
    )

@rt.message(CommandStart())
async def Start_Comand(message: Message, state: FSMContext):
    is_admin_user = message.chat.type == 'private' or await is_admin(message.from_user.id,
                                                                     message.chat.id)
    if not is_admin_user:
        return
    try:
        if not await db.user_exists(message.chat.id):
            await db.add_user(message.chat.id, '-', '-', message.message_thread_id)
    except Exception as e:
        await bot.send_message(admins[0], f"Произошла ошибка: {e}")
    await state.update_data(branch=message.text)
    non_admin = [
            [
                KeyboardButton(text='Меню🏠'),
                KeyboardButton(text='Профиль🔑')
            ]
        ]
    admin = [
            [
                KeyboardButton(text='Меню🏠'),
                KeyboardButton(text='Профиль🔑')
            ],
            [
                KeyboardButton(text="Выгрузка расписания🗒")
            ]
        ]
    if message.chat.id in admins:
        keyboard = admin
    else:
        keyboard = non_admin
    await message.answer(f"Привет! Измените информацию о вашем филиале и смене в меню, чтобы получать расписание. ✍️", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))
    await home(message, state)



@rt.callback_query(F.data == 'get_shift')
async def settings_shift(query: CallbackQuery, state: FSMContext):
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                                    query.message.chat.id)
    if not is_admin_user:
        return
    await state.set_state(Form.shift)
    await query.message.edit_text("Выберите смену, по которой вы хотите получать расписание: \n\n",
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [
                                     InlineKeyboardButton(text='Первая смена1️⃣', callback_data='Первая смена1️⃣'),
                                     InlineKeyboardButton(text='Вторая смена2️⃣', callback_data='Вторая смена2️⃣'),

                                 ],
                                 [
                                     InlineKeyboardButton(text='Обе смены(1️⃣+2️⃣)', callback_data='Обе смены(1️⃣+2️⃣)'),
                                 ],
                             ]
                         ))


@rt.callback_query(Form.shift)
async def handle_shift(query: CallbackQuery, state: FSMContext):
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                           query.message.chat.id)
    if not is_admin_user:
        await state.clear()
        return
    shift = await get_shift(query.data)
    try:
        await db.change_photo_value(query.message.chat.id, shift)
    except Exception as e:
        await bot.send_message(admins[0], f"Произошла ошибка: {e}")
    await query.message.edit_text(f"Отлично! Теперь вы будете получать расписание!\nСмена: {query.data}.")
    await menu(query.message, state)

async def get_shift(text: str) -> int:
    if text == 'Первая смена1️⃣':
        return 1
    if text == 'Вторая смена2️⃣':
        return 2
    if text == 'Обе смены(1️⃣+2️⃣)':
        return 3
    else:
        return 0


@rt.callback_query(F.data == 'get_branch')
async def settings_branch(query: CallbackQuery, state: FSMContext):
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                                    query.message.chat.id)
    if not is_admin_user:
        return
    await state.set_state(Form.branch)
    await query.message.edit_text("Теперь выберите ваш филиал:\n\n",
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [
                                     InlineKeyboardButton(text='Гидрострой', callback_data='Гидрострой'),
                                 ],
                                 [
                                     InlineKeyboardButton(text='Сахарова', callback_data='Сахарова'),
                                     InlineKeyboardButton(text='Макеева', callback_data='Макеева'),
                                 ]
                             ],
                         ))

@rt.callback_query(Form.branch)
async def handle_branch(query: CallbackQuery, state: FSMContext):
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                           query.message.chat.id)
    if not is_admin_user:
        await state.clear()
        return
    try:
        await db.change_branch_value(query.message.chat.id, query.data)
    except Exception as e:
        await bot.send_message(admins[0], f"Произошла ошибка: {e}")
    await query.message.edit_text(f"Отлично! Теперь ваш филиал: {query.data}")
    await menu(query.message, state)


@rt.callback_query(F.data == 'schedule')
async def get_schedule(query: CallbackQuery):
    await bot.answer_callback_query(query.id)
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                                    query.message.chat.id)
    if not is_admin_user:
        return
    await query.message.answer("👌")
    try:
        data = await db.get_user_data(query.message.chat.id)
    except Exception as e:
        await bot.send_message(admins[0], f'Произошла ошибка {e}')
    if data[3] != '-' and data[2] != 0:
        try:
            photos = await db.get_photos(data[3])
        except Exception as e:
            await bot.send_message(admins[0], f'Произошла ошибка {e}')
        if len(photos) == 0:
            await query.message.answer("Расписания пока нет.")
        for photo in photos:
            if photo[1] == data[3] and (data[2] == 3 or data[2] == photo[2]):
                await bot.send_photo(query.message.chat.id, photo=photo[0])
    else:
        await query.message.answer("Вы не выбрали свой филиал, либо смену в меню")



@rt.callback_query(F.data == 'get_group')
async def settings_class(query: CallbackQuery, state: FSMContext):
    is_admin_user = query.message.chat.type == 'private' or await is_admin(query.from_user.id,
                                                                           query.message.chat.id)
    if not is_admin_user:
        return
    await bot.answer_callback_query(query.id)
    await state.set_state(Form.group_name)
    await query.message.answer("Введите номер вашего класса.\nНапример: 11.1, 8Г")

@rt.message(Form.group_name)
async def handle_class(message: Message, state: FSMContext):
    try:
        await db.change_class_value(message.chat.id, message.text)
    except Exception as e:
        await bot.send_message(admins[0], f"Произошла ошибка: {e}")
    await message.answer(f"Отлично! Теперь ваш класс: {message.text}")
    await menu(message, state)

@rt.message(F.text == 'Выгрузка расписания🗒')
async def admin_tree(message: Message, state: FSMContext):
    await message.answer('👇')
    try:
        data = await db.get_user_data(message.chat.id)
    except Exception as e:
        await bot.send_message(admins[0], f"Ошибка:{e}")
    if data[3] != '-':
        await message.answer("Выберите смену расписания на фото, также можете выгрузить таблицу с расписанием:", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Первая смена", callback_data='first_shift'),
                    InlineKeyboardButton(text='Вторая смена', callback_data='second_shift')
                ],
                [
                  InlineKeyboardButton(text='Выгрузить таблицу с расписанием', callback_data='add_table')
                ],
            ]
        ))
    else:
        await message.answer("Для начала выберите ваш филиал, чтобы выгружать расписание!")
        await menu(message, state)

@rt.callback_query(F.data == 'first_shift')
async def handle_first_shift(query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(query.id)
    await state.set_state(Form.add_shift)
    await state.update_data(shift=1)
    await query.message.answer("Теперь отправьте фотографию с расписанием первой смены.")


@rt.callback_query(F.data == 'second_shift')
async def handle_first_shift(query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(query.id)
    await state.set_state(Form.add_shift)
    await state.update_data(shift=2)
    await query.message.answer("Теперь отправьте фотографию с расписанием первой смены.")

@rt.message(Form.add_shift, F.photo)
async def add_shift(message: Message, state: FSMContext):
    data = await state.get_data()
    shift = data['shift']
    try:
        udata = await db.get_user_data(message.chat.id)
    except Exception as e:
        await bot.send_message(admins[0], f"Ошибка:{e}")

    await message.reply("Фото обрабатывается... (Это может занять несколько секунд)")

    try:
        file_id = message.photo[-1].file_id
        try:
            photos = await db.get_photos(udata[3])
            print(photos)
        except Exception as e:
            await bot.send_message(admins[0], f"Плачевно.")
        if len(photos) >= 2:
            await db.delete_photos(udata[3])
            await db.add_photo(file_id, udata[3], shift)
        else:
            await db.add_photo(file_id, udata[3], shift)
        # Получение пользователей, которым нужно отправить фото
        rows = await db.get_users_by_branch(udata[3])
        target_users = [row for row in rows if row[2] == shift or row[2] == 3]
        await send_photos_in_batches(target_users, file_id)
        await message.answer("Фото успешно обработано!")
        await state.clear()
        await admin_tree(message, state)

    except Exception as e:
        await bot.send_message(admins[0], f"Произошла ошибка: {e}\nПожалуйста, обратитесь к @XorKoT")


async def send_photos_in_batches(users, photo_id):
    """
    Отправляет фото пользователям партиями для избежания лимита Telegram API.
    """
    batch_size = 30
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        tasks = []

        for user in batch:
            tasks.append(send_photo_safe(user[0], photo_id, user[4]))

        await asyncio.gather(*tasks)
        await asyncio.sleep(1)


async def send_photo_safe(chat_id, photo_id, thread_id):
    """
    Безопасная отправка фото. Обрабатывает ошибки и удаляет неактивных пользователей.
    """
    try:
        await bot.send_photo(chat_id, photo=photo_id, message_thread_id=thread_id)
    except TelegramNotFound:
        await db.delete_user(chat_id)
    except TelegramForbiddenError:
        await db.delete_user(chat_id)
    except TelegramUnauthorizedError:
        await db.delete_user(chat_id)
    except TelegramBadRequest:
        await db.delete_user(chat_id)
    except Exception as e:
        logging.error(f"Ошибка при отправке фото пользователю {chat_id}: {e}")

@rt.callback_query(F.data == 'add_table')
async def add_table(query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(query.id)
    await query.message.answer("Теперь отправьте файл с таблицей расписания в формате .XLSX")
    await state.set_state(Form.table)

@rt.message(Form.table, F.content_type == ContentType.DOCUMENT)
async def handle_table(message: Message, state: FSMContext):
    data = await db.get_user_data(message.chat.id)
    if data[3] == '-':
        await message.answer("Вы не выбрали филиал!")
        await menu(message, state)
        return
    if message.document.mime_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        await message.answer("Отправьте таблицу в формате xlsx!")
    else:
        document_id = message.document.file_id
        await Bot.download(bot,document_id,"table.xlsx",120)
        try:
            await message.answer("Таблица обрабатывается. Это может занять несколько секунд.")
            await db.update_table("table.xlsx", data[3])
            notifier.clear_scheduled_messages()
            for user in await db.get_all_users():
                    if user[4] != '-':
                        lessons = await db.get_lessons(user[2], user[4])
                        notifier.handle_table(lessons, user[0])
            await message.answer('✍️')
            await message.answer("Готово! Таблица успешно обработана!")
            await admin_tree(message, state)
        except Exception as e:
            await bot.send_message(admins[0], f"Произошла ошибка {e}")



# Дебаговые штучки:

@rt.message(Command("global_msg"))
async def global_message(message: Message, state: FSMContext):
    await state.set_state(Form.global_msg)
    await message.reply("Жду сообщения")

@rt.message(Form.global_msg)
async def handle_global(message: Message, state: FSMContext):
    try:
        users = await db.get_all_users()
    except Exception as e:
        await message.answer(f"GG {e}")
    for user in users:
        if int(user[1]) > 0:
            try:
                await bot.send_message(user[1], message.text)
            except Exception as e:
                await message.answer(f'Ошибка {e}')
    await state.clear()

@rt.message(Command("secret_"))
async def check_users(message: Message):
    try:
        data = await db.get_all_users()
    except Exception as e:
        await message.answer(f'Ошибка {e}')
    for user in data:
        try:
            chat = await bot.get_chat(chat_id=user[1])
            name = chat.first_name
            await message.answer(f'{name}: {user[1:]}')
            await asyncio.sleep(0.5)
        except Exception as e:
            await message.answer(f'Ошибка: {e}')


async def main():
    dp = Dispatcher()
    dp.include_router(rt)
    await notifier.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())