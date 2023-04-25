from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery,Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
import sqlite3
import os


import config #містить токен бота (https://t.me/FP_individual_project_Bot)


bot = Bot(token=config.TOKET)
dp = Dispatcher(bot, storage=MemoryStorage())


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
        keyboard.add(types.InlineKeyboardButton(text="Керування теоретичним навчальним матеріалом", callback_data="theoretical_matirials_manage"))
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
    
    
######## Блок індивідуальне завдання N3 (Кротко) ########

#меню практичних
@dp.callback_query_handler(lambda query: query.data == "practical_matirials_manage")
async def process_pr_query(callback_query: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Завантажити нову ПР", callback_data="practical_matirials_manage_add"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити існуючу ПР", callback_data="practical_matirials_manage_remove"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити ПР за конкретною темою", callback_data="practical_matirials_manage_themeRemove"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Практичні роботи:", reply_markup=keyboard)


#блок додавання нового ПР
@dp.callback_query_handler(lambda query: query.data == "practical_matirials_manage_add")
async def process_pr_query_add(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"practical_matirials_manage_add_theme_{theme[0]}"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)
    conn.close()


# обнраємо тему та запитуємо назву
@dp.callback_query_handler(lambda query: query.data.startswith("practical_matirials_manage_add_theme_"))
async def process_pr_query_add(callback_query: types.CallbackQuery):
    theme_id = callback_query.data.split("practical_matirials_manage_add_theme_")[1]
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Введіть назву практичної роботи:")
    await dp.current_state().set_state('waiting_for_practical_material_title')
    await dp.current_state().update_data(theme_id=theme_id)


# вводимо назву ПР та запитуємо файл
async def process_pr_query_add_title(message: types.Message):
    practical_material_title = message.text
    await bot.send_message(chat_id=message.chat.id, text="Надішліть файл практичної роботи:")
    await dp.current_state().set_state('waiting_for_practical_material_file')
    await dp.current_state().update_data(practical_material_title=practical_material_title)


# зберігаємо фалй та додаємо запис в БД
async def process_pr_query_add_file(message: types.Message):
    data = await dp.current_state().get_data()
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    file_path = os.path.join("Files", "PracticalMaterials", message.document.file_name)
    await bot.download_file_by_id(message.document.file_id, file_path)
    cur.execute("INSERT INTO practical_tasks (id, theme_id, title, content) VALUES (?, ?, ?, ?)", (None, data['theme_id'], data['practical_material_title'], file_path))
    conn.commit()
    conn.close()
    await bot.send_message(chat_id=message.chat.id, text=f"Практична робота '{data['practical_material_title']}' додана.")
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="practical_matirials_manage"))
    await bot.send_message(chat_id=message.chat.id, text=f"Повернутись до меню ПР?", reply_markup=keyboard)
    
    await dp.current_state().reset_state(with_data=False)


dp.register_message_handler(process_pr_query_add_title, state='waiting_for_practical_material_title') # стадія отримання назви
dp.register_message_handler(process_pr_query_add_file, state='waiting_for_practical_material_file', content_types=['document']) # стадія отримання файлу
#кінець блоку додавання ПР

#блок видалення ПР
# виводимо інлайн кнопки з переліком практичних (видалення конкретної ПР)
@dp.callback_query_handler(lambda query: query.data == "practical_matirials_manage_remove")
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM practical_tasks")
    pws = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for pw in pws:
        keyboard.add(types.InlineKeyboardButton(text=pw[2], callback_data=f"practical_matirials_manage_remove_pr_{pw[0]}"))   
         
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть практичну котру необхідно видалить:", reply_markup=keyboard)    
    conn.close()
    
   
# процес видалення ПР (видалення конкретної ПР) 
@dp.callback_query_handler(lambda query: query.data.startswith("practical_matirials_manage_remove_pr_"))
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    pw_id = callback_query.data.split("practical_matirials_manage_remove_pr_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM practical_tasks WHERE id = ?", (pw_id,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM practical_tasks WHERE id = ?", (pw_id,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="practical_matirials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню ПР?", reply_markup=keyboard)
    

# видалення практичних за темами, виводим кнопки з переліком тем   
@dp.callback_query_handler(lambda query: query.data == "practical_matirials_manage_themeRemove")
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"practical_matirials_manage_themeRemove_theme_{theme[0]}"))
        
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)  
    conn.close()
    

# отримуємо тему та видаляємо всі практичні з цією темою 
@dp.callback_query_handler(lambda query: query.data.startswith("practical_matirials_manage_themeRemove_theme_"))
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    theme = callback_query.data.split("practical_matirials_manage_themeRemove_theme_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM practical_tasks WHERE theme_id = ?", (theme,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM practical_tasks WHERE theme_id = ?", (theme,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="practical_matirials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню ПР?", reply_markup=keyboard)
    
#кінець блоку видалення ПР
############ кінець блоку N3 ###############

######## Блок індивідуальне завдання N1 (Петрук) ########

#меню теоретичного матеріалу#
@dp.callback_query_handler(lambda query: query.data == "theoretical_matirials_manage")
async def process_pr_query(callback_query: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Завантажити нову лекцію", callback_data="theoretical_materials_manage_add"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити існуючу лекцію", callback_data="theoretical_materials_manage_remove"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити лекцію за конкретною темою", callback_data="theoretical_materials_manage_themeRemove"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Лекції:", reply_markup=keyboard)

#Блок додавання нової лекції#

@dp.callback_query_handler(Text(equals="theoretical_materials_manage_add"))
async def process_pr_query_add(callback_query: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"theoretical_materials_manage_add_theme_{theme[0]}"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)
    conn.close()

#Обираємо тему та запитуємо назву#


@dp.callback_query_handler(lambda query: query.data.startswith("theoretical_materials_manage_add_theme_"))
async def process_pr_query_add(callback_query: CallbackQuery, state: FSMContext):
    theme_id = callback_query.data.split("theoretical_materials_manage_add_theme_")[1]
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Введіть назву лекції:")
    await state.set_state('waiting_for_theoretical_material_title')
    await state.update_data(theme_id=theme_id)

#вводимо назву лекції та запитуємо файл#

@dp.message_handler(state='waiting_for_theoretical_material_title')
async def process_pr_query_add_title(message: Message, state: FSMContext):
    theoretical_material_title = message.text
    await bot.send_message(chat_id=message.chat.id, text="Надішліть файл лекції:")
    await state.set_state('waiting_for_theoretical_material_file')
    await state.update_data(theoretical_material_title=theoretical_material_title)

#зберігаємо файл та додаємо запис в БД#

async def process_pr_query_add_file(message: Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    file_path = os.path.join("Files", "TheoreticalMaterials", message.document.file_name)
    await bot.download_file_by_id(message.document.file_id, file_path)
    cur.execute("INSERT INTO theoretical_materials (id, theme_id, title, content) VALUES (?, ?, ?, ?)", (None, data['theme_id'], data['theoretical_material_title'], file_path))
    conn.commit()
    conn.close()
    await bot.send_message(chat_id=message.chat.id, text=f"Лекція '{data['theoretical_material_title']}' додана.")
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="theoretical_matirials_manage"))
    await bot.send_message(chat_id=message.chat.id, text=f"Повернутись до меню лекції?", reply_markup=keyboard)
    
    await state.reset_state(with_data=False)

dp.register_message_handler(process_pr_query_add_file, state='waiting_for_theoretical_material_file', content_types=['document'])

#кінець блоку додавання лекції

#блок видалення лекції
# виводимо інлайн кнопки з переліком практичних (видалення конкретної лекції)

@dp.callback_query_handler(text="theoretical_materials_manage_remove")
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM theoretical_materials")
    pws = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for pw in pws:
        keyboard.add(types.InlineKeyboardButton(text=pw[2], callback_data=f"theoretical_materials_manage_remove_pr_{pw[0]}"))   
         
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть лекцію котру необхідно видалить:", reply_markup=keyboard)    
    conn.close()

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("theoretical_materials_manage_remove_pr_"))
async def process_theoretical_material_removal(callback_query: types.CallbackQuery):
    pr_id = int(callback_query.data.split('_')[-1])
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM theoretical_materials WHERE id=?", (pr_id,))
    conn.commit()
    conn.close()
    await bot.send_message(chat_id=callback_query.message.chat.id, text=f"Лекція з ID {pr_id} видалена.")
    await bot.answer_callback_query(callback_query.id)

# процес видалення лекції (видалення конкретної лекції) 

@dp.callback_query_handler(lambda query: query.data.startswith("theoretical_materials_manage_remove_pr_"))
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    pw_id = callback_query.data.split("theoretical_materials_manage_remove_pr_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM theoretical_materials WHERE id = ?", (pw_id,))
    pws = cur.fetchall()
    
    for pw in pws:
        file_path = pw[3]
        if os.path.exists(file_path):
            os.remove(file_path)
        
    cur.execute("DELETE FROM theoretical_materials WHERE id = ?", (pw_id,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="theoretical_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню лекцій?", reply_markup=keyboard)

# видалення лекцій за темами, виводим кнопки з переліком тем   

@dp.callback_query_handler(text="theoretical_materials_manage_themeRemove")
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"theoretical_materials_manage_themeRemove_theme_{theme[0]}"))
        
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)
    conn.close()

# отримуємо тему та видаляємо всі практичні з цією темою 

@dp.callback_query_handler(lambda query: query.data.startswith("theoretical_materials_manage_themeRemove_theme_"))
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    theme = callback_query.data.split("theoretical_materials_manage_themeRemove_theme_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM theoretical_materials WHERE theme_id = ?", (theme,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM theoretical_materials WHERE theme_id = ?", (theme,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="theoretical_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню лекції?", reply_markup=keyboard)
    #кінець блока видалення
   #кінець завдання N1 (Петрук)
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
