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
        keyboard.add(types.InlineKeyboardButton(text="Керування матеріалом для практичних робіт", callback_data="practical_matirials_manage"))
        
        await bot.send_message(chat_id=message.chat.id, text="Меню:", reply_markup=keyboard)

######## Блок індивідуальне завдання N7 (Ярослав) ########

#Вивід даних для звичайного користувача (поверхневе, просто вивожу дані з бд, у кого по завданню перероблюйте)

def all_teory_requests(user_id):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM ready_unverified_user_tasks")
    end = cur.fetchall()

    cur.execute("SELECT * FROM theoretical_materials")
    out = cur.fetchall()

    for row in out[:]:
        
        if any(str(row[0]) == str(e[1]).replace('read_', '') and int(user_id) == int(e[2])  for e in end):
            print(out)
            out.remove(row)

    conn.close()
    return out


def all_end(user_id):
    result = []
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM ready_unverified_user_tasks")
    end = cur.fetchall()

    cur.execute("SELECT * FROM theoretical_materials")
    out = cur.fetchall()

    for row in out[:]:
        
        if any(str(row[0]) == str(e[1]).replace('read_', '') and int(user_id) == int(e[2])  for e in end):
            print(row)
            result.append(row)

    conn.close()
    return result

@dp.message_handler(text="Теоретичні матеріали")
async def all_theory_for_student(message: types.Message):
    all_teory = all_teory_requests(message.chat.id)

    if(all_teory):
        for file in all_teory:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Прочитано", callback_data="read_"+str(file[0])))   
            await bot.send_message(chat_id=message.chat.id, text=str(file).replace(',','\n').translate(str.maketrans({'(': None, ')': None, "'": None})),reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=message.chat.id, text="Завдань нема\n")

@dp.message_handler(text="Завершено")
async def all_end_tasks(message: types.Message):
    end = all_end(message.chat.id)

    if(end):
        for file in end:   
            await bot.send_message(chat_id=message.chat.id, text=str(file).replace(',','\n').translate(str.maketrans({'(': None, ')': None, "'": None})))
    else:
        await bot.send_message(chat_id=message.chat.id, text="Завдань нема\n")

@dp.message_handler(text="Практичні роботи та тести")
async def all_tasks(message: types.Message):
    conn = sqlite3.connect('FP.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM practical_tasks")
    all_tasks = cur.fetchall()

    await bot.send_message(chat_id=message.chat.id, text="Практичні завдання:\n")

    if(all_tasks):
        for file in all_tasks:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Прикріпити файл", callback_data="prac_"+str(file[0])))
            await bot.send_message(chat_id=message.chat.id, text=str(file).replace(',','\n').translate(str.maketrans({'(': None, ')': None, "'": None})),reply_markup=keyboard)
    
        cur.execute("SELECT * FROM test_tasks") #Вивід тесту некоректний, на момент добавлення, повністью нереалізовані тести, виводятся питання
        all_tests = cur.fetchall()
    else:
        await bot.send_message(chat_id=message.chat.id, text="Нових практичних нема\n")
    await bot.send_message(chat_id=message.chat.id, text="Тести:\n")

    if(all_tasks):
        for file in all_tests:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Пройти", callback_data="answer_"+str(file[0])))
            await bot.send_message(chat_id=message.chat.id, text=str(file).replace(',','\n').translate(str.maketrans({'(': None, ')': None, "'": None})),reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=message.chat.id, text="Нових тестів нема\n")
    conn.close()

########################### Кінець ###########################

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

######## Блок індивідуальне завдання N7 (Ярослав) ########
@dp.callback_query_handler(lambda query: query.data.startswith("read_"))
async def read_teory(callback_query: types.CallbackQuery):    
    conn = sqlite3.connect('FP.db')
    user_id = callback_query.from_user.id
    cur = conn.cursor()
    cur.execute("INSERT INTO ready_unverified_user_tasks (all_tasks, user_id) VALUES (?, ?)", (callback_query.data, user_id))
    conn.commit()
 
    await bot.send_message(chat_id=user_id, text="Інші не прочитані завдання\n")
    all_teory = all_teory_requests(user_id)

    if(all_teory):
        for file in all_teory:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Прочитано", callback_data="read_"+str(file[0])))   
            await bot.send_message(chat_id=user_id, text=str(file).replace(',','\n').translate(str.maketrans({'(': None, ')': None, "'": None})),reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=user_id, text="Завдань нема\n")
   
        
    conn.close()



########################### Кінець ###########################


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
    #Клавіатура для виведення матеріалів та їх історія
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    theory_button = types.KeyboardButton(text="Теоретичні матеріали")
    practice_button = types.KeyboardButton(text="Практичні роботи та тести")
    completed_button = types.KeyboardButton(text="Завершено")
    keyboard.add(theory_button, practice_button)
    keyboard.add(completed_button)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Ви успішно додані до вибраної групи!", reply_markup=keyboard)
    
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


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
