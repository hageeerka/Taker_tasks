import telebot
from telebot import types

token = '6933495351:AAEIm3hBl79gABYjaUaQvd0_o2WQ7pUEpeM'
bot = telebot.TeleBot(token)
temp_data = {}
all_tasks = {}
task_id = None


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

    if data.startswith('priority'):
        all_tasks[task_id]['priority'] = int(data.split('_')[1])
        buttons = [
            {'text': 'Всё верно', 'callback_data': 'l'},
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


def set_director(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id in temp_data and temp_data[chat_id]["director_id"] is None:
        username = message.text.strip()
        if username.startswith("@"):
            temp_data[chat_id]["director_id"] = username
            buttons = [
                {'text': 'Создать новую задачу', 'callback_data': 'add_task'},
                {'text': 'Распределить роли', 'callback_data': 'assign_roles'}
            ]
            text = 'Отлично! Теперь вы можете распределить роли и поставить первые задачи.'
            send_message_with_inline_keyboard(chat_id, text, buttons)
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
        {'text': 'Всё верно', 'callback_data': 'l'},
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
        {'text': 'Всё верно', 'callback_data': 'l'},
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
        {'text': 'Всё верно', 'callback_data': 'l'},
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


bot.polling(none_stop=True)
