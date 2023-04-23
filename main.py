from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
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
        keyboard.add(types.InlineKeyboardButton(text="Керування додатковим матеріалом ", callback_data="additional_materials_manage"))
    # кнопка для додавання користувальницького додаткового матеріалу(додавання запису в таблицю user_materials)
    elif (existing_user[2] == 0):
         keyboard.add(types.InlineKeyboardButton(text="Запит на додавання додаткового матеріалу користувача", callback_data="additional_materials_user_request"))  


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
    
    


######## Блок індивідуальне завдання N6 (Савицький) ########


#додавання користувальницького додаткового матеріалу
@dp.callback_query_handler(lambda query: query.data == "additional_materials_user_request")
async def process_pr_query_add(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"additional_materials_user_request_theme_{theme[0]}"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)
    conn.close()

# обираємо тему та запитуємо назву
@dp.callback_query_handler(lambda query: query.data.startswith("additional_materials_user_request_theme_"))
async def process_pr_query_add(callback_query: types.CallbackQuery):
    theme_id = callback_query.data.split("additional_materials_user_request_theme_")[1]
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Введіть назву додаткового матеріалу:")
    await dp.current_state().set_state('waiting_for_user_additional_material_title')
    await dp.current_state().update_data(theme_id=theme_id)

# вводимо назву додаткового матеріалу та запитуємо файл
async def process_pr_query_add_title(message: types.Message):
    additional_user_material_title = message.text
    await bot.send_message(chat_id=message.chat.id, text="Надішліть файл додаткового матеріалу:")
    await dp.current_state().set_state('waiting_for_user_additional_material_file')
    await dp.current_state().update_data(additional_user_material_title=additional_user_material_title)

# зберігаємо файл та додаємо запис в БД
async def process_pr_query_add_file(message: types.Message):
    data = await dp.current_state().get_data()
    conn = sqlite3.connect('FP.db')
    user_id = message.from_user.id
    cur = conn.cursor()
    file_path = os.path.join("Files", "AdditionalMaterials", message.document.file_name)
    await bot.download_file_by_id(message.document.file_id, file_path)
    cur.execute("INSERT INTO user_materials (id, user_id, theme_id, material_name, file_link) VALUES (?,?, ?, ?, ?)", (None, user_id, data['theme_id'], data['additional_user_material_title'], file_path))
    conn.commit()
    conn.close()
    await bot.send_message(chat_id=message.chat.id, text=f"Додатковий матеріал'{data['additional_user_material_title']}' доданий.")
    
    
    await dp.current_state().reset_state(with_data=False)


dp.register_message_handler(process_pr_query_add_title, state='waiting_for_user_additional_material_title')
dp.register_message_handler(process_pr_query_add_file, state='waiting_for_user_additional_material_file', content_types=['document']) 

# кінець додавання користувальницького додаткового матеріалу

#меню для додаткових матеріалів
@dp.callback_query_handler(lambda query: query.data == "additional_materials_manage")
async def process_pr_query(callback_query: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Завантажити додатковий матеріал", callback_data="additional_materials_manage_add"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити додатковий матеріал", callback_data="additional_materials_manage_remove"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити додатковий матеріал користувача", callback_data="user_materials_manage_remove"))
    keyboard.add(types.InlineKeyboardButton(text="Видалити додатковий матеріал за конкретною темою", callback_data="additional_materials_manage_themeRemove"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Додатковий матеріал:", reply_markup=keyboard)

#додавання нового додаткового матеріалу
@dp.callback_query_handler(lambda query: query.data == "additional_materials_manage_add")
async def process_pr_query_add(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"additional_materials_manage_add_theme_{theme[0]}"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)
    conn.close()

# обираємо тему та запитуємо назву
@dp.callback_query_handler(lambda query: query.data.startswith("additional_materials_manage_add_theme_"))
async def process_pr_query_add(callback_query: types.CallbackQuery):
    theme_id = callback_query.data.split("additional_materials_manage_add_theme_")[1]
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Введіть назву додаткового матеріалу:")
    await dp.current_state().set_state('waiting_for_additional_material_title')
    await dp.current_state().update_data(theme_id=theme_id)

# вводимо назву додаткового матеріалу та запитуємо файл
async def process_pr_query_add_title(message: types.Message):
    additional_material_title = message.text
    await bot.send_message(chat_id=message.chat.id, text="Надішліть файл додаткового матеріалу:")
    await dp.current_state().set_state('waiting_for_additional_material_file')
    await dp.current_state().update_data(additional_material_title=additional_material_title)

# зберігаємо файл та додаємо запис в БД
async def process_pr_query_add_file(message: types.Message):
    data = await dp.current_state().get_data()
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    file_path = os.path.join("Files", "AdditionalMaterials", message.document.file_name)
    await bot.download_file_by_id(message.document.file_id, file_path)
    cur.execute("INSERT INTO additional_materials (id, theme_id, title, content) VALUES (?, ?, ?, ?)", (None, data['theme_id'], data['additional_material_title'], file_path))
    conn.commit()
    conn.close()
    await bot.send_message(chat_id=message.chat.id, text=f"Додатковий матеріал'{data['additional_material_title']}' доданий.")
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="additional_materials_manage"))
    await bot.send_message(chat_id=message.chat.id, text=f"Повернутись до меню додаткових матеріалів?", reply_markup=keyboard)
    
    await dp.current_state().reset_state(with_data=False)


dp.register_message_handler(process_pr_query_add_title, state='waiting_for_additional_material_title') # стадія отримання назви
dp.register_message_handler(process_pr_query_add_file, state='waiting_for_additional_material_file', content_types=['document']) # стадія отримання файлу
#кінець додавання нового додаткового матеріалу

#видалення додаткового матеріалу користувача
@dp.callback_query_handler(lambda query: query.data == "user_materials_manage_remove")
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_materials")
    pws = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for pw in pws:
        keyboard.add(types.InlineKeyboardButton(text=pw[3], callback_data=f"user_materials_manage_remove_am_{pw[0]}"))   
         
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть матеріал котрий необхідно видалить:", reply_markup=keyboard)    
    conn.close()

# процес видалення (видалення конкретного додаткового матеріалу користувача)
@dp.callback_query_handler(lambda query: query.data.startswith("user_materials_manage_remove_am_"))
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    pw_id = callback_query.data.split("user_materials_manage_remove_am_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_materials WHERE id = ?", (pw_id,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM user_materials WHERE id = ?", (pw_id,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="additional_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню додаткових матеріалів?", reply_markup=keyboard)
# кінець видалення додаткового матеріалу користувача

# видалення додаткових матеріалів користувача за конкретною темою
@dp.callback_query_handler(lambda query: query.data == "user_materials_manage_themeRemove")
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"user_materials_manage_themeRemove_theme_{theme[0]}"))
        
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)  
    conn.close()

# отримуємо тему та видаляємо всі матеріали з цією темою 
@dp.callback_query_handler(lambda query: query.data.startswith("user_materials_manage_themeRemove_theme_"))
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    theme = callback_query.data.split("user_materials_manage_themeRemove_theme_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_materials WHERE theme_id = ?", (theme,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM user_materials WHERE theme_id = ?", (theme,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="additional_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню додаткових матеріалів?", reply_markup=keyboard)
# кінець видалення додаткових матеріалів користувача за конкретною темою


# видалення конкретного додаткового матеріалу
@dp.callback_query_handler(lambda query: query.data == "additional_materials_manage_remove")
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM additional_materials")
    pws = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for pw in pws:
        keyboard.add(types.InlineKeyboardButton(text=pw[2], callback_data=f"additional_materials_manage_remove_am_{pw[0]}"))   
         
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть матеріал котрий необхідно видалить:", reply_markup=keyboard)    
    conn.close()

#процес видалення (видалення конкретного додаткового матеріалу)
@dp.callback_query_handler(lambda query: query.data.startswith("additional_materials_manage_remove_am_"))
async def process_pr_query_remove(callback_query: types.CallbackQuery):
    pw_id = callback_query.data.split("additional_materials_manage_remove_am_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM additional_materials WHERE id = ?", (pw_id,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM additional_materials WHERE id = ?", (pw_id,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="additional_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню додаткових матеріалів?", reply_markup=keyboard)
# кінець видалення конкретного додаткового матеріалу

# видалення додаткових матеріалів  за конкретною темою
@dp.callback_query_handler(lambda query: query.data == "additional_materials_manage_themeRemove")
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM themes")
    themes = cur.fetchall()
    keyboard = types.InlineKeyboardMarkup()
    
    for theme in themes:
        keyboard.add(types.InlineKeyboardButton(text=theme[1], callback_data=f"additional_materials_manage_themeRemove_theme_{theme[0]}"))
        
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Оберіть тему:", reply_markup=keyboard)  
    conn.close()
    

# отримуємо тему та видаляємо всі матеріали з цією темою 
@dp.callback_query_handler(lambda query: query.data.startswith("additional_materials_manage_themeRemove_theme_"))
async def process_pr_query_themeRemove(callback_query: types.CallbackQuery):
    theme = callback_query.data.split("additional_materials_manage_themeRemove_theme_")[1]
    
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM additional_materials WHERE theme_id = ?", (theme,))
    pws = cur.fetchall()
    
    for pw in pws:
        try:
            os.remove(pw[3])
        except:
            pass
        
    cur.execute("DELETE FROM additional_materials WHERE theme_id = ?", (theme,))
    conn.commit()
    conn.close()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Повернутись назад до меню", callback_data="additional_materials_manage"))
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Успішно видалено!\n Повернутись до меню додаткових матеріалів?", reply_markup=keyboard)

#кінець видалення додаткових матеріалів  за конкретною темою
############ кінець блоку N6 ###############
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
