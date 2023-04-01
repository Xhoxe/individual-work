from aiogram import Bot, Dispatcher, executor, types
import sqlite3
import config


bot = Bot(token=config.TOKET)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    conn = sqlite3.connect('FP.db')
    user_id = message.from_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user is None:
        await bot.send_message(chat_id=message.chat.id, text="Будь-ласка введіть своє ім'я:")


@dp.message_handler(commands=['menu'])
async def send_welcome(message: types.Message):
    conn = sqlite3.connect('FP.db')
    user_id = message.from_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    existing_user = cur.fetchone()
    
    #під свій пункт створювати окрему кнопку
    if (existing_user[2] == 1):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Керування матеріалом для практичних робіт", callback_data="practical_matirials_manage"))
        
        await bot.send_message(chat_id=message.chat.id, text="Меню:", reply_markup=keyboard)


#спрацбовує лише у випадку якщо користувача немає в БД
@dp.message_handler()
async def check_if_user_exists(message: types.Message):
    conn = sqlite3.connect('FP.db')
    user_id = message.from_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user is None:
        await process_name(message)
        
    conn.close()


#лове інлайн для прикріпленя групи до студента
@dp.callback_query_handler(lambda query: query.data.startswith("set_group_to_new_user_"))
async def check_and_process_callback_query(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    user_id = callback_query.from_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user is not None:
        await process_callback_query(callback_query)
        
    conn.close()


#отримує введене ім'я та прівзищє (також у випадку якщо користувача немає в БД)
async def process_name(message: types.Message):
    conn = sqlite3.connect('FP.db')
    user_id = message.from_user.id
    cur = conn.cursor()
    cur.execute("SELECT * FROM groups")
    groups = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for group in groups:
        keyboard.add(types.InlineKeyboardButton(text=group[1], callback_data=f"set_group_to_new_user_{group[0]}"))
        
    name_user = message.text
    query = "INSERT INTO users (id, username, role, `group`) VALUES (?, ?, ?, ?)"
    cur.execute(query, (user_id, name_user, 0, None)) #роль на "1" (адміна/викладача) міняти вручну в БД, у майбудньому в кого завдання містить цей пункт опрацює це
    conn.commit()
    await bot.send_message(chat_id=message.chat.id, text="Будь-ласка оберіть групу:", reply_markup=keyboard)
    
    conn.close()


#встановлює групу студенту
async def process_callback_query(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    user_id = callback_query.from_user.id
    group = callback_query.data.split("set_group_to_new_user_")[1]
    query = "UPDATE users SET `group`=? WHERE id=?"
    cur = conn.cursor()
    cur.execute(query, (group, user_id))
    conn.commit()
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Ви успішно додані до вибраної групи!")
    
    conn.close()
    
    
#блок індивідуальне завдання N3 (Кротко)

async def process_pr_query(callback_query: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Завантажити нову ПР", callback_data="practical_matirials_add"))
    keyboard.add(types.InlineKeyboardButton(text="Змінити існуючу ПР", callback_data="practical_matirials_change"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити існуючу ПР", callback_data="practical_matirials_remove"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Практичні роботи:", reply_markup=keyboard)
    
###############################


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
