import telebot
from telebot import types

token = '6933495351:AAEIm3hBl79gABYjaUaQvd0_o2WQ7pUEpeM'
bot = telebot.TeleBot(token)
temp_data = {}
all_tasks = {}
my_team = {}
task_id = None
member_id = None


def send_message_with_inline_keyboard(chat_id, text, buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['callback_data']))
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    text = 'Привет! Я Чат-бот Трекер задач, готов помочь вам с организацией работы над проектом.' \
           'Вместе мы сможем эффективно достигать поставленных целей.' \
           'Для начала назначьте должность Руководителя.'
    buttons = [{'text': 'Добавить руководителя', 'callback_data': 'add_director'}]
    send_message_with_inline_keyboard(chat_id, text, buttons)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == 'add_director':
        temp_data[chat_id] = {"director_id": None}
        bot.send_message(chat_id, "Напишите @username руководителя")
        bot.register_next_step_handler(call.message, set_director)

    if data == 'add_task':
        global task_id
        task_id = 'task_' + str(len(all_tasks) + 1)
        all_tasks[task_id] = {"name": None, 'description': None, 'deadline': None, 'responsible': None, 'priority': None}
        bot.send_message(chat_id, "Напишите название задачи")
        bot.register_next_step_handler(call.message, set_name)
    if data == 'edit_task':
        if len(all_tasks)!=0:
            text = 'Список задач:\n'
            for i in range(len(all_tasks)):
                task_id = 'task_'+str(i+1)
                text += f"Задача № {i+1}\n"\
                        f"Название:{all_tasks[task_id]['name']}\n" \
                        f"Описание: {all_tasks[task_id]['description']}\n" \
                        f"Дедлайн: {all_tasks[task_id]['deadline']}\n" \
                        f"Приоритет: {all_tasks[task_id]['priority']}\n"
            bot.send_message(chat_id, text=text)
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'edit_task_{i}') for i in range(1, len(all_tasks)+1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите задачу, которую хотите изменить', reply_markup=markup)
    if data == 'edit_name':
        bot.send_message(chat_id, 'Напишите название задачи')
        bot.register_next_step_handler(call.message, edit_name)

    if data == 'edit_description':
        bot.send_message(chat_id, 'Напишите описание задачи')
        bot.register_next_step_handler(call.message, edit_description)

    if data == 'edit_deadline':
        bot.send_message(chat_id, 'Напишите дедлайн задачи')
        bot.register_next_step_handler(call.message, edit_deadline)

    if data == 'edit_priority':
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(str(i), callback_data=f'priority_{i}') for i in range(1, 6)]
        markup.add(*buttons)
        bot.send_message(chat_id, text='Выберите приоритет задачи.', reply_markup=markup)
    if data == 'menu':
        show_menu(chat_id=chat_id)
    if data.startswith('priority'):
        all_tasks[task_id]['priority'] = int(data.split('_')[1])
        buttons = [
            {'text': 'Всё верно', 'callback_data': 'menu'},
            {'text': 'Изменить название', 'callback_data': 'edit_name'},
            {'text': 'Изменить описание', 'callback_data': 'edit_description'},
            {'text': 'Изменить дедлайн', 'callback_data': 'edit_deadline'},
            {'text': 'Изменить приоритет', 'callback_data': 'edit_priority'}
        ]
        text = f"Ваша задача создана, проверьте информацию.\n" \
               f"Название: {all_tasks[task_id]['name']}\n" \
               f"Описание: {all_tasks[task_id]['description']}\n" \
               f"Дедлайн: {all_tasks[task_id]['deadline']}\n" \
               f"Приоритет: {all_tasks[task_id]['priority']}"
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data.startswith('edit_task_'):
        task_id = 'task_'+ data[-1]
        buttons = [
            {'text': 'Изменить название', 'callback_data': 'edit_name'},
            {'text': 'Изменить описание', 'callback_data': 'edit_description'},
            {'text': 'Изменить дедлайн', 'callback_data': 'edit_deadline'},
            {'text': 'Изменить приоритет', 'callback_data': 'edit_priority'}
        ]
        send_message_with_inline_keyboard(chat_id, 'Выберите, что именно хотите изменить в вашей задаче', buttons)
    if data == 'assign_roles':
        bot.send_message(chat_id, 'Напишите username')
        bot.register_next_step_handler(call.message, set_username)
    if data == 'show_team':
        if len(my_team)==0:
            bot.send_message(chat_id=chat_id, text='На данный момент ваша команда не сформирована, добавьте участников, чтобы исправить это.')
        else:
            text = ''
            for i in range(len(my_team)):
                text+=my_team[i]
    if data == 'add_member':
        global member_id
        member_id = 'member_' + str(len(my_team) + 1)
        my_team[member_id] = {"username": None, 'firstname': None, 'lastname': None, 'role': None}
        bot.send_message(chat_id, "Напишите username участника, которого хотите добавить в команду.")
        bot.register_next_step_handler(call.message, set_username)
    if data == 'team':
        buttons = [
            {'text': 'Показать список участников', 'callback_data': 'show_team'},
            {'text': 'Добавить участника', 'callback_data': 'add_member'},
            {'text': 'Удалить участника', 'callback_data': 'delete_member'},
            {'text': 'Редактировать участника', 'callback_data': 'edit_member'}
        ]
        send_message_with_inline_keyboard(chat_id, 'Выберите, что хотите сделать с участником команды.', buttons)


def show_menu(chat_id):
    buttons = [
        {'text': 'Создать новую задачу', 'callback_data': 'add_task'},
        {'text': 'Распределить роли', 'callback_data': 'assign_roles'},
        {'text': 'Моя команда', 'callback_data': 'team'},
        {'text': 'Редактировать задачу', 'callback_data': 'edit_task'}
    ]
    text = 'Отлично! Теперь вы можете распределить роли и поставить первые задачи.'
    send_message_with_inline_keyboard(chat_id, text, buttons)
def set_director(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id in temp_data and temp_data[chat_id]["director_id"] is None:
        username = message.text.strip()
        if username.startswith("@"):
            temp_data[chat_id]["director_id"] = username
            show_menu(chat_id=chat_id)
        else:
            bot.send_message(chat_id, 'Пожалуйста, напишите правильный @username руководителя')


def set_name(message):
    chat_id = message.chat.id
    if all_tasks[task_id]['name'] is None:
        all_tasks[task_id]['name'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите описание задачи')
        bot.register_next_step_handler(message, set_description)


def edit_name(message):
    chat_id = message.chat.id
    all_tasks[task_id]['name'] = message.text.strip()
    buttons = [
        {'text': 'Всё верно', 'callback_data': 'menu'},
        {'text': 'Изменить название', 'callback_data': 'edit_name'},
        {'text': 'Изменить описание', 'callback_data': 'edit_description'},
        {'text': 'Изменить дедлайн', 'callback_data': 'edit_deadline'},
        {'text': 'Изменить приоритет', 'callback_data': 'edit_priority'}
    ]
    text = f"Ваша задача создана, проверьте информацию.\n" \
           f"Название: {all_tasks[task_id]['name']}\n" \
           f"Описание: {all_tasks[task_id]['description']}\n" \
           f"Дедлайн: {all_tasks[task_id]['deadline']}\n" \
           f"Приоритет: {all_tasks[task_id]['priority']}"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_description(message):
    chat_id = message.chat.id
    if all_tasks[task_id]['description'] is None and all_tasks[task_id]['name'] is not None:
        all_tasks[task_id]['description'] = message.text.strip()
        bot.send_message(chat_id, 'Установите дедлайн. Укажите дату и время в формате date.month.year hours:minutes, например 24.06.2023 18:00')
        bot.register_next_step_handler(message, set_deadline)


def edit_description(message):
    chat_id = message.chat.id
    all_tasks[task_id]['description'] = message.text.strip()
    buttons = [
        {'text': 'Всё верно', 'callback_data': 'menu'},
        {'text': 'Изменить название', 'callback_data': 'edit_name'},
        {'text': 'Изменить описание', 'callback_data': 'edit_description'},
        {'text': 'Изменить дедлайн', 'callback_data': 'edit_deadline'},
        {'text': 'Изменить приоритет', 'callback_data': 'edit_priority'}
    ]
    text = f"Ваша задача создана, проверьте информацию.\n" \
           f"Название: {all_tasks[task_id]['name']}\n" \
           f"Описание: {all_tasks[task_id]['description']}\n" \
           f"Дедлайн: {all_tasks[task_id]['deadline']}\n" \
           f"Приоритет: {all_tasks[task_id]['priority']}"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_deadline(message):
    chat_id = message.chat.id
    if all_tasks[task_id]['deadline'] is None and all_tasks[task_id]['name'] is not None and all_tasks[task_id]['description'] is not None:
        all_tasks[task_id]['deadline'] = message.text.strip()
        buttons = [types.InlineKeyboardButton(str(i), callback_data=f'priority_{i}') for i in range(1, 6)]
        markup = types.InlineKeyboardMarkup()
        markup.add(*buttons)
        bot.send_message(chat_id, text='Выберите приоритет задачи.', reply_markup=markup)


def edit_deadline(message):
    chat_id = message.chat.id
    all_tasks[task_id]['deadline'] = message.text.strip()
    buttons = [
        {'text': 'Всё верно', 'callback_data': 'menu'},
        {'text': 'Изменить название', 'callback_data': 'edit_name'},
        {'text': 'Изменить описание', 'callback_data': 'edit_description'},
        {'text': 'Изменить дедлайн', 'callback_data': 'edit_deadline'},
        {'text': 'Изменить приоритет', 'callback_data': 'edit_priority'}
    ]
    text = f"Ваша задача создана, проверьте информацию.\n" \
           f"Название: {all_tasks[task_id]['name']}\n" \
           f"Описание: {all_tasks[task_id]['description']}\n" \
           f"Дедлайн: {all_tasks[task_id]['deadline']}\n" \
           f"Приоритет: {all_tasks[task_id]['priority']}"
    send_message_with_inline_keyboard(chat_id, text, buttons)
def set_username(message):
    chat_id = message.chat.id
    if my_team[member_id]['username'] is None:
        my_team[member_id]['username'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите имя участника')
        bot.register_next_step_handler(message, set_firstname)
def set_firstname(message):
    chat_id = message.chat.id
    if my_team[member_id]['username'] is not None and my_team[member_id]['firstname'] is None:
        my_team[member_id]['firstname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите фамилию участника')
        bot.register_next_step_handler(message, set_lastname)
def set_lastname(message):
    chat_id = message.chat.id
    if my_team[member_id]['username'] is not None and my_team[member_id]['firstname'] is not None and my_team[member_id]['lastname'] is None:
        my_team[member_id]['lastname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите роль участника')
        bot.register_next_step_handler(message, set_role)
def set_role(message):
    chat_id = message.chat.id
    if my_team[member_id]['username'] is not None and my_team[member_id]['firstname'] is not None and \
            my_team[member_id]['lastname'] is not None and my_team[member_id]['role'] is None:
        my_team[member_id]['role'] = message.text.strip()
        buttons = [
            {'text': 'всё верно, вернуться в меню', 'callback_data': 'team'}
        ]
        text = f"Участник создан, проверьте информацию.\n" \
               f"@username: {my_team[member_id]['username']}\n" \
               f"Имя: {my_team[member_id]['firstname']}\n" \
               f"Фамилия: {my_team[member_id]['lastname']}\n" \
               f"Роль: {my_team[member_id]['role']}"
        print(my_team)
        send_message_with_inline_keyboard(chat_id, text, buttons)


bot.polling(none_stop=True)
