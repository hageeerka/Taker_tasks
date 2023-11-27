import telebot
from telebot import types
from typing import Optional
import json
import os
import fnmatch
import requests

token = '6856368403:AAFdgiN2KyqflfVZyCl6bXsqfbJDNujV5BI'
bot = telebot.TeleBot(token)
temp_data = {}
all_tasks = {}
my_team = {}
task_id = None
member_id = None


def save_my_team(id_member):
    file_path = f"C:/Users/timofei/Desktop/моё/json/m{id_member}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(my_team[id_member], file, ensure_ascii=False)


def load_my_team(id_member):
    file_path = f"C:/Users/timofei/Desktop/моё/json/m{id_member}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            my_team[id_member].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


def save_all_tasks(id_member):
    file_path = f"C:/Users/timofei/Desktop/моё/json/a{id_member}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(all_tasks[id_member], file, ensure_ascii=False)


def load_all_tasks(id_member):
    file_path =  f"C:/Users/timofei/Desktop/моё/json/a{id_member}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            all_tasks[id_member].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


def save_temp_data(id_member):
    file_path =  f"C:/Users/timofei/Desktop/моё/json/t{id_member}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(temp_data[id_member], file, ensure_ascii=False)


def load_temp_data(id_member):
    file_path = f"C:/Users/timofei/Desktop/моё/json/t{id_member}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            temp_data[id_member].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


@bot.message_handler(commands=['load'])
def handle_save_command(message):
    id_member = message.from_user.id
    load_my_team(id_member)
    load_temp_data(id_member)
    load_all_tasks(id_member)
    bot.reply_to(message, 'Данные успешно загружены!')


@bot.message_handler(commands=['save'])
def handle_save_command(message):
    id_member = message.from_user.id
    save_my_team(id_member)
    save_temp_data(id_member)
    save_all_tasks(id_member)
    bot.reply_to(message, 'Данные успешно сохранены!')


def send_message_with_inline_keyboard(chat_id, text, buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['callback_data']))
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    chat_id = message.chat.id
    show_menu(chat_id)


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    text = f'Привет!👋🏼\nЯ Чат-бот Трекер задач, готов помочь вам с организацией работы над проектом. \n' \
           'Вместе мы сможем эффективно достигать поставленных целей. \n' \
           '*Для начала назначьте должность Руководителя.* '
    buttons = [{'text': '▶️Добавить руководителя', 'callback_data': 'add_director'}]
    temp_data[id_member] = {}
    all_tasks[id_member] = {}
    my_team[id_member] = {}
    send_message_with_inline_keyboard(chat_id, text, buttons)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    id_member = call.from_user.id
    data = call.data

    if data == 'add_director':
        temp_data[id_member][chat_id] = {"director_id": None}
        bot.send_message(chat_id, "Напишите @username руководителя")
        bot.register_next_step_handler(call.message, set_director)

    if data == 'add_task':
        global task_id
        task_id = 'task_' + str(len(all_tasks[id_member]) + 1)
        all_tasks[id_member][task_id] = {"name": None, 'description': None, 'deadline': None, 'responsible': None,
                                         'priority': None}
        bot.send_message(chat_id, "Напишите название задачи")
        bot.register_next_step_handler(call.message, set_name)
    if data == 'edit_task':
        if len(all_tasks[id_member]) != 0:
            text = '*Список задач*:\n'
            for i in range(len(all_tasks[id_member])):
                task_id = 'task_' + str(i + 1)
                text += f"_Задача № {i + 1}_\n" \
                        f"Название:{all_tasks[id_member][task_id]['name']}\n" \
                        f"Описание: {all_tasks[id_member][task_id]['description']}\n" \
                        f"Дедлайн: {all_tasks[id_member][task_id]['deadline']}\n" \
                        f"Приоритет: {all_tasks[id_member][task_id]['priority']}\n"
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
            '''markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'edit_task_{i}') for i in
                       range(1, len(all_tasks[id_member]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите задачу, которую хотите изменить', reply_markup=markup)'''
            buttons = []
            for i in range(1, len(all_tasks[id_member]) + 1):
                buttons.append({'text': str(i), 'callback_data': f'edit_task_{i}'})
            buttons.append({'text': '🔙Вернуться назад', 'callback_data': 'menu'})
            text = 'Выберите задачу, которую хотите изменить'
            send_message_with_inline_keyboard(chat_id, text, buttons)

    if data == 'all_tasks':
        show_all_tasks(chat_id, message_id, id_member)

    if data.startswith('show_member_tasks'):
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(my_team[id_member]['member_' + str(i)]['username'], callback_data=f'show_tasks_for_member_{i}') for i in range(1, len(my_team[id_member]) + 1)]
        markup.add(*buttons)
        edit_message_text(chat_id, message_id, text='Выбери участника, для которого хочешь посмотреть задачи',
                          reply_markup=markup)

    if data.startswith('show_tasks_for_member_'):
        global member_id
        member_id = 'member_'+data[-1]
        tasks = []
        buttons = []
        text = 'Выберите задачу, информация о которой вам интересна. Задачи расположены в порядке приоритета от наиболее важных к наименее важным.'
        for task_id in all_tasks[id_member]:
            if all_tasks[id_member][task_id]['responsible'] is not None:
                if my_team[id_member][member_id]['username'] in all_tasks[id_member][task_id]['responsible']:
                    tasks.append(task_id)
        for num_priority in range(1,6):
            for task_id in tasks:
                if num_priority == int(all_tasks[id_member][task_id]['priority']):
                    buttons.append({'text': all_tasks[id_member][task_id]['name'], 'callback_data': f'show_task_{task_id[-1]}_for_member_{member_id[-1]}'})
        edit_message_with_inline_keyboard(chat_id, message_id, text, buttons)

    if data.startswith('show_task_'):
        task_id = 'task_'+data[10]
        member_id = 'member_'+data[-1]
        text = f"_Задача № {task_id[-1]}_\n" \
                f"Название:{all_tasks[id_member][task_id]['name']}\n" \
                f"Описание: {all_tasks[id_member][task_id]['description']}\n" \
                f"Дедлайн: {all_tasks[id_member][task_id]['deadline']}\n" \
                f"Приоритет: {all_tasks[id_member][task_id]['priority']}\n"
        buttons = [
            {'text': '🔙Выбрать другую задачу', 'callback_data': f'show_tasks_for_member_{task_id[-1]}'},
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        edit_message_with_inline_keyboard(chat_id, message_id, text, buttons)

    if data == 'return_menu':
        show_menu(chat_id)

    if data == 'return_all_tasks':
        show_all_tasks(chat_id, message_id, id_member)

    if data == 'completed_tasks':
        completed_tasks = [task_id for task_id, task_info in all_tasks[id_member].items() if
                           task_info.get('completed', False)]
        if not completed_tasks:
            text = 'Нет выполненных задач.'
        else:
            text = 'Выполненные задачи:\n'
            for i, task_id in enumerate(completed_tasks, start=1):
                text += f"{i}. {all_tasks[id_member][task_id]['name']}\n"
        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data == 'uncompleted_tasks':
        uncompleted_tasks = [task_id for task_id, task_info in all_tasks[id_member].items() if
                             not task_info.get('completed', False)]
        if not uncompleted_tasks:
            text = 'Нет невыполненных задач.'
        else:
            text = 'Невыполненные задачи:\n'
            for i, task_id in enumerate(uncompleted_tasks, start=1):
                text += f"{i}. {all_tasks[id_member][task_id]['name']}\n"
        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data == 'change_status':
        text = 'Выберите задачу для изменения статуса:'
        buttons = [
            {'text': f'{i + 1}. {task_info["name"]}', 'callback_data': f'change_status_{task_id}'}
            for i, (task_id, task_info) in enumerate(all_tasks[id_member].items())
        ]
        buttons.append({'text': 'Назад', 'callback_data': 'return_all_tasks'})
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data.startswith('change_status_'):
        task_id_to_change = data.replace('change_status_', '')
        if task_id_to_change in all_tasks[id_member]:
            task_info = all_tasks[id_member][task_id_to_change]
            current_status = task_info.get('completed', False)
            new_status = not current_status
            task_info['completed'] = new_status
            text = f"Статус задачи изменен на {'Выполнена' if new_status else 'Не выполнена'}."
        else:
            text = "Задача не найдена."

        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

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
        bot.send_message(chat_id, text='Выберите приоритет задачи', reply_markup=markup)
    if data == 'menu':
        show_menu(chat_id=chat_id)
    if data.startswith('priority'):
        all_tasks[id_member][task_id]['priority'] = int(data.split('_')[1])
        if len(my_team[id_member]) == 0:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'add_member'}
            ]
        else:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
            ]
        text = f"Ваша задача создана, проверьте информацию.\n" \
               f"🔸*Название*: {all_tasks[id_member][task_id]['name']}\n" \
               f"🔸*Описание*: {all_tasks[id_member][task_id]['description']}\n" \
               f"🔸*Дедлайн*: {all_tasks[id_member][task_id]['deadline']}\n" \
               f"🔸*Приоритет*: {all_tasks[id_member][task_id]['priority']}\n" \
               "P.S. Изменить задачу вы можете в разделе 'Главное меню'"
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data.startswith('edit_task_'):
        task_id = 'task_' + data[-1]
        buttons = [
            {'text': '⚫️Изменить название', 'callback_data': 'edit_name'},
            {'text': '🔵️Изменить описание', 'callback_data': 'edit_description'},
            {'text': '⚫️Изменить дедлайн', 'callback_data': 'edit_deadline'},
            {'text': '🔵️Изменить приоритет', 'callback_data': 'edit_priority'},
            {'text': '❌Удалить задачу', 'callback_data': 'delete_task'},
            {'text': '🔙Вернуться назад', 'callback_data': 'edit_task'}

        ]
        send_message_with_inline_keyboard(chat_id, 'Выберите, что именно хотите изменить в вашей задаче', buttons)
    if data == 'delete_task':
        for i in range(int(task_id[-1]), len(all_tasks)):
            all_tasks[id_member]['task_' + str(i)] = all_tasks['task_' + str(i + 1)]
        del all_tasks[id_member]['task_' + str(len(all_tasks))]
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Эта задача была удалена из списка.'
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'add_member':
        additional_text = ''
        if len(my_team[id_member]) == 0:
            additional_text = 'Теперь вам необходимо добавить первого участника в команду. '
        member_id = 'member_' + str(len(my_team[id_member]) + 1)
        my_team[id_member][member_id] = {"username": None, 'firstname': None, 'lastname': None, 'role': None}
        bot.send_message(chat_id, f"{additional_text}Напишите @username участника, которого хотите добавить в команду.")
        bot.register_next_step_handler(call.message, set_username)
    if data.startswith('edit_member_'):
        member_id = 'member_' + data[-1]
        buttons = [
            {'text': 'Изменить @username', 'callback_data': 'edit_username'},
            {'text': 'Изменить имя', 'callback_data': 'edit_firstname'},
            {'text': 'Изменить фамилию', 'callback_data': 'edit_lastname'},
            {'text': 'Изменить роль', 'callback_data': 'edit_role'}
        ]
        send_message_with_inline_keyboard(chat_id, 'Выберите, какую именно информацию об участнике хотите изменить',
                                          buttons)
    if data == 'edit_username':
        bot.send_message(chat_id, 'Напишите @username')
        bot.register_next_step_handler(call.message, edit_username)
    if data == 'edit_firstname':
        bot.send_message(chat_id, 'Напишите имя')
        bot.register_next_step_handler(call.message, edit_firstname)
    if data == 'edit_lastname':
        bot.send_message(chat_id, 'Напишите фамилию')
        bot.register_next_step_handler(call.message, edit_lastname)
    if data == 'edit_role':
        bot.send_message(chat_id, 'Напишите роль')
        bot.register_next_step_handler(call.message, edit_role)
    if data.startswith('del_member_'):
        member_id_number = int(data[-1])
        for i in range(member_id_number, len(my_team[id_member])):
            my_team[id_member]['member_' + str(i)] = my_team[id_member]['member_' + str(i + 1)]
        del my_team[id_member]['member_' + str(len(my_team[id_member]))]
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Этот участник был удалён из команды.'
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'delete_member':
        if len(my_team[id_member]) != 0:
            markup = types.InlineKeyboardMarkup()
            buttons = [
                types.InlineKeyboardButton(my_team[id_member]['member_' + str(i)]['username'],
                                           callback_data=f'del_member_{i}') for
                i in
                range(1, len(my_team[id_member]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите участника, которого хотите удалить из команды.',
                             reply_markup=markup)
    if data.startswith('add_responsible_member_'):
        all_tasks[id_member][f'task_{data[23]}']['responsible'] = 'member_' + str(data[-1])
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Отлично, участник закреплён за задачей!'
        send_message_with_inline_keyboard(chat_id, text, buttons)

    if data.startswith('add_responsible_for_task_'):
        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton(my_team[id_member]['member_' + str(i)]['username'],
                                       callback_data=f'add_responsible_member_{i}_for_task_{str(data[-1])}') for
            i in
            range(1, len(my_team[id_member]) + 1)]
        markup.add(*buttons)
        bot.send_message(chat_id, text='Выберите участника, которого хотите закрепить за задачей.',
                         reply_markup=markup)
    if data == 'assign_roles':
        if len(all_tasks[id_member]) != 0:
            text = '*Список задач*:\n'
            for i in range(len(all_tasks[id_member])):
                task_id = 'task_' + str(i + 1)
                text += f"_Задача № {i + 1}_\n" \
                        f"Название:{all_tasks[id_member][task_id]['name']}\n" \
                        f"Описание: {all_tasks[id_member][task_id]['description']}\n" \
                        f"Дедлайн: {all_tasks[id_member][task_id]['deadline']}\n" \
                        f"Приоритет: {all_tasks[id_member][task_id]['priority']}\n"
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'assign_members_to_task_{i}') for i in
                       range(1, len(all_tasks[id_member]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите задачу, за которой хотите закрепить участника',
                             reply_markup=markup)
    if data.startswith('assign_members_to_task_'):
        all_tasks[id_member]['task_' + data[-1]]['responsible'] = None
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(my_team[id_member]['member_' + str(i)]['username'],
                                              callback_data=f'assign_member_{i}_for_task_{data[-1]}') for i in
                   range(1, len(my_team[id_member]) + 1)]
        buttons += {types.InlineKeyboardButton('Готово!',
                                               callback_data=f'ready_to_assign')}
        markup.add(*buttons)
        bot.send_message(chat_id,
                         text='Нажмите на @username всех участников, которые будет закреплены за задачей. Затем нажмите кнопку "Готово!"',
                         reply_markup=markup)
    if data.startswith('assign_member_'):
        task_id = 'task_' + data[-1]
        if all_tasks[id_member][task_id]['responsible'] is None:
            all_tasks[id_member][task_id]['responsible'] = [my_team[id_member]['member_' + data[14]]['username']]
        else:
            all_tasks[id_member][task_id]['responsible'] += [my_team[id_member]['member_' + data[14]]['username']]
    if data == 'ready_to_assign':
        text = f"Отлично, теперь за задачей под названием {all_tasks[id_member][task_id]['name']} закреплен(ы) участник(и) с @username {all_tasks[id_member][task_id]['responsible']}"
        buttons = [
            {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'show_team':
        if len(my_team[id_member]) == 0:
            text = 'На данный момент ваша команда не сформирована, добавьте участников, чтобы исправить это.'
        else:
            text = "Список участников:\n"
            for i in range(len(my_team[id_member])):
                show_member_id = 'member_' + str(i + 1)
                text += f"*Участник № {i + 1}\n*" \
                        f"🔸@username: {my_team[id_member][show_member_id]['username']}\n" \
                        f"🔸Имя: {my_team[id_member][show_member_id]['firstname']}\n" \
                        f"🔸Фамилия: {my_team[id_member][show_member_id]['lastname']}\n" \
                        f"🔸Роль: {my_team[id_member][show_member_id]['role']}\n"
        buttons = [
            {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'team':
        buttons = [
            {'text': '🚻Показать список участников', 'callback_data': 'show_team'},
            {'text': '🆕Добавить участника', 'callback_data': 'add_member'},
            {'text': '🔄Редактировать участника', 'callback_data': 'edit_member'},
            {'text': '❌Удалить участника', 'callback_data': 'delete_member'},
            {'text': '🔙Вернуться назад', 'callback_data': 'menu'}
        ]
        send_message_with_inline_keyboard(chat_id, 'Выберите, что хотите сделать с участником команды.', buttons)
    if data == 'edit_member':
        if len(my_team[id_member]) != 0:
            text = 'Список участников:\n'
            for i in range(len(my_team[id_member])):
                show_member_id = 'member_' + str(i + 1)
                text += f"Участник № {i + 1}\n" \
                        f"🔸@username: {my_team[id_member][show_member_id]['username']}\n" \
                        f"🔸Имя: {my_team[id_member][show_member_id]['firstname']}\n" \
                        f"🔸Фамилия: {my_team[id_member][show_member_id]['lastname']}\n" \
                        f"🔸Роль: {my_team[id_member][show_member_id]['role']}\n"
            bot.send_message(chat_id, text=text)
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'edit_member_{i}') for i in
                       range(1, len(my_team[id_member]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите участника, информацию о котором вы хотите изменить',
                             reply_markup=markup)
    if data == 'gpt':
        buttons = [
            {'text': 'Назад', 'callback_data': 'menu'}
        ]
        text = 'Попросите совета у нейросети'
        send_message_with_inline_keyboard(chat_id, text, buttons)
        bot.register_next_step_handler(call.message, neuroask)

def neuroask(message):
    chat_id = message.chat.id
    url = "https://llm.api.cloud.yandex.net/llm/v1alpha/chat"
    data = {
        "model": "general",
        "generationOptions": {
            "partialResults": True,
            "temperature": 0.4,
            "maxTokens": 200
        },
        "messages": [
            {
                "role": "ai.languageModels.user",
                "text":message.text.strip()
                }
        ],
        "instructionText": "ты умная нейросеть и помогаешь людям решать рабочие проблемы",
    }
    headers = {"Authorization": f'Api-Key {"AQVNwWtHH04wz-RRaNbCS4DH1cMfJdp67NmvF4e0"}',
                }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        first_ans = json.loads(response.text.split('}\n')[-2]+'}')
        bot.send_message(chat_id, first_ans['result']['message']['text'])
    else:
        buttons = [
            {'text': 'Назад', 'callback_data': 'menu'}
        ]
        text = 'Извините, что-то пошло не так'
        send_message_with_inline_keyboard(chat_id, text, buttons)


def show_menu(chat_id):
    buttons = [
        {'text': '➕Создать новую задачу', 'callback_data': 'add_task'},
        {'text': '📝Распределить участников по задачам', 'callback_data': 'assign_roles'},
        {'text': '🔝Моя команда', 'callback_data': 'team'},
        {'text': '✏️Редактировать задачу', 'callback_data': 'edit_task'},
        {'text': '📚Ваши задачи', 'callback_data': 'all_tasks'},
        {'text': 'Попросить совет', 'callback_data': 'gpt'}
    ]
    text = 'Отлично! Теперь вы можете распределить роли и поставить задачи.'
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_director(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if chat_id in temp_data[id_member] and temp_data[id_member][chat_id]["director_id"] is None:
        username = message.text.strip()
        if username.startswith("@"):
            temp_data[id_member][chat_id]["director_id"] = username
            buttons = [
                {'text': '➕Создать новую задачу', 'callback_data': 'add_task'}
            ]
            text = 'Отлично! Теперь вам необходимо создать первую задачу.'
            send_message_with_inline_keyboard(chat_id, text, buttons)
            '''task_id = 'task_' + str(len(all_tasks) + 1)
        all_tasks[task_id] = {"name": None, 'description': None, 'deadline': None, 'responsible': None,
                              'priority': None}
        bot.send_message(chat_id, "Напишите название задачи")
        bot.register_next_step_handler(call.message, set_name)'''

        else:
            bot.send_message(chat_id, '*Пожалуйста, напишите @username в верном формате.*', parse_mode='Markdown')
            bot.register_next_step_handler(message, set_director)


def set_name(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if all_tasks[id_member][task_id]['name'] is None:
        all_tasks[id_member][task_id]['name'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите описание задачи')
        bot.register_next_step_handler(message, set_description)


def edit_name(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    all_tasks[id_member][task_id]['name'] = message.text.strip()
    if len(my_team[id_member]) == 0:
        buttons = [
            {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'add_member'}
        ]
    else:
        buttons = [
            {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
        ]
    text = f"Информация о задаче изменена.\n" \
           f"🔸*Название*: {all_tasks[id_member][task_id]['name']}\n" \
           f"🔸*Описание*: {all_tasks[id_member][task_id]['description']}\n" \
           f"🔸*Дедлайн*: {all_tasks[id_member][task_id]['deadline']}\n" \
           f"🔸*Приоритет*: {all_tasks[id_member][task_id]['priority']}\n" \
           "P.S. изменить задачу вы можете в разделе 'Главное меню'"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_description(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if all_tasks[id_member][task_id]['description'] is None and all_tasks[id_member][task_id]['name'] is not None:
        all_tasks[id_member][task_id]['description'] = message.text.strip()
        bot.send_message(chat_id,
                         'Установите дедлайн. Укажите дату и время в формате date.month.year hours:minutes, например 24.06.2023 18:00')
        bot.register_next_step_handler(message, set_deadline)


def edit_description(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    all_tasks[id_member][task_id]['description'] = message.text.strip()
    if len(my_team[id_member]) == 0:
        buttons = [
            {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'add_member'}
        ]
    else:
        buttons = [
            {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
        ]
    text = f"Информация о задаче изменена.\n" \
           f"🔸*Название*: {all_tasks[id_member][task_id]['name']}\n" \
           f"🔸*Описание*: {all_tasks[id_member][task_id]['description']}\n" \
           f"🔸*Дедлайн*: {all_tasks[id_member][task_id]['deadline']}\n" \
           f"🔸*Приоритет*: {all_tasks[id_member][task_id]['priority']}\n" \
           "P.S. изменить задачу вы можете в разделе 'Главное меню'"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_deadline(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if all_tasks[id_member][task_id]['deadline'] is None and all_tasks[id_member][task_id]['name'] is not None and \
            all_tasks[id_member][task_id][
                'description'] is not None:
        if fnmatch.fnmatch(message.text, "??.??.???? ??:??"):
            all_tasks[id_member][task_id]['deadline'] = message.text.strip()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'priority_{i}') for i in range(1, 6)]
            markup = types.InlineKeyboardMarkup()
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите приоритет задачи.', reply_markup=markup)
        else:
            new_message = bot.send_message(chat_id, '*Пожалуйста, укажите дедлайн формате date.month.year hours:minutes.*', parse_mode='Markdown')
            bot.register_next_step_handler(new_message, set_deadline)


def edit_deadline(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    all_tasks[id_member][task_id]['deadline'] = message.text.strip()
    if fnmatch.fnmatch(message.text, "??.??.???? ??:??"):
        if len(my_team[id_member]) == 0:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'add_member'}
            ]
        else:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
            ]
        text = f"Информация о задаче изменена.\n" \
               f"🔸*Название*: {all_tasks[id_member][task_id]['name']}\n" \
               f"🔸*Описание*: {all_tasks[id_member][task_id]['description']}\n" \
               f"🔸*Дедлайн*: {all_tasks[id_member][task_id]['deadline']}\n" \
               f"🔸*Приоритет*: {all_tasks[id_member][task_id]['priority']}\n" \
               "P.S. изменить задачу вы можете в разделе 'Главное меню'"
        send_message_with_inline_keyboard(chat_id, text, buttons)
    else:
        new_message = bot.send_message(chat_id, '*Пожалуйста, укажите дедлайн формате date.month.year hours:minutes.*', parse_mode='Markdown')
        bot.register_next_step_handler(new_message, edit_deadline)


def set_username(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if my_team[id_member][member_id]['username'] is None:
        my_team[id_member][member_id]['username'] = message.text.strip()
        if my_team[id_member][member_id]['username'].startswith('@'):
            bot.send_message(chat_id, 'Напишите имя участника')
            bot.register_next_step_handler(message, set_firstname)
        else:
            my_team[id_member][member_id]['username'] = None
            bot.send_message(chat_id, '*Пожалуйста, введите @username в верном формате.*', parse_mode = 'Markdown')
            bot.register_next_step_handler(message, set_username)

def edit_username(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if message.text.startswith('@'):
        if len(my_team[id_member]) == 0:
            my_team[id_member][member_id]['username'] = message.text.strip()
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
            ]
        else:
            buttons = [
                {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
            ]
            text = f"Информация об участнике изменена.\n" \
                   f"🔸@username: {my_team[id_member][member_id]['username']}\n" \
                   f"🔸Имя: {my_team[id_member][member_id]['firstname']}\n" \
                   f"🔸Фамилия: {my_team[id_member][member_id]['lastname']}\n" \
                   f"🔸Роль: {my_team[id_member][member_id]['role']}\n" \
                   "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
        send_message_with_inline_keyboard(chat_id, text, buttons)
    else:
        bot.send_message(chat_id, '*Пожалуйста, введите @username в верном формате.*', parse_mode = 'Markdown')
        bot.register_next_step_handler(message, edit_username)


def set_firstname(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if my_team[id_member][member_id]['username'] is not None and my_team[id_member][member_id]['firstname'] is None:
        my_team[id_member][member_id]['firstname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите фамилию участника')
        bot.register_next_step_handler(message, set_lastname)


def edit_firstname(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    my_team[id_member][member_id]['firstname'] = message.text.strip()
    buttons = [
        {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
    ]
    text = f"Информация об участнике изменена.\n" \
           f"🔸@username: {my_team[id_member][member_id]['username']}\n" \
           f"🔸Имя: {my_team[id_member][member_id]['firstname']}\n" \
           f"🔸Фамилия: {my_team[id_member][member_id]['lastname']}\n" \
           f"🔸Роль: {my_team[id_member][member_id]['role']}\n" \
           "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_lastname(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if my_team[id_member][member_id]['username'] is not None and my_team[id_member][member_id][
        'firstname'] is not None and \
            my_team[id_member][member_id]['lastname'] is None:
        my_team[id_member][member_id]['lastname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите роль участника')
        bot.register_next_step_handler(message, set_role)


def edit_lastname(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    my_team[id_member][member_id]['lastname'] = message.text.strip()
    buttons = [
        {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
    ]
    text = f"Информация об участнике изменена.\n" \
           f"🔸@username: {my_team[id_member][member_id]['username']}\n" \
           f"🔸Имя: {my_team[id_member][member_id]['firstname']}\n" \
           f"🔸Фамилия: {my_team[id_member][member_id]['lastname']}\n" \
           f"🔸Роль: {my_team[id_member][member_id]['role']}\n" \
           "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_role(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    if my_team[id_member][member_id]['username'] is not None and my_team[id_member][member_id][
        'firstname'] is not None and \
            my_team[id_member][member_id]['lastname'] is not None and my_team[id_member][member_id]['role'] is None:
        my_team[id_member][member_id]['role'] = message.text.strip()
        buttons = [
            {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = f"Участник создан, проверьте информацию.\n" \
               f"🔸@username: {my_team[id_member][member_id]['username']}\n" \
               f"🔸Имя: {my_team[id_member][member_id]['firstname']}\n" \
               f"🔸Фамилия: {my_team[id_member][member_id]['lastname']}\n" \
               f"🔸Роль: {my_team[id_member][member_id]['role']}\n" \
               "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
        send_message_with_inline_keyboard(chat_id, text, buttons)


def edit_role(message):
    chat_id = message.chat.id
    id_member = message.from_user.id
    my_team[id_member][member_id]['role'] = message.text.strip()
    buttons = [
        {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
    ]
    text = f"Информация об участнике изменена.\n" \
           f"🔸@username: {my_team[id_member][member_id]['username']}\n" \
           f"🔸Имя: {my_team[id_member][member_id]['firstname']}\n" \
           f"🔸Фамилия: {my_team[id_member][member_id]['lastname']}\n" \
           f"🔸Роль: {my_team[id_member][member_id]['role']}\n" \
           "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def show_all_tasks(chat_id, message_id, id_member):
    text = '*Все задачи:*\n'
    for i, task_id in enumerate(all_tasks[id_member].keys(), start=1):
        task_info = all_tasks[id_member][task_id]
        status = "_Выполнена_" if task_info.get('completed', False) else "_Не выполнена_"
        text += f"{i}. {task_info['name']} - {status}\n"
    buttons = [
        {'text': '🔙Вернуться в Главное меню', 'callback_data': 'return_menu'},
        {'text': '❌Невыполненные задачи', 'callback_data': 'uncompleted_tasks'},
        {'text': '✅Выполненные задачи', 'callback_data': 'completed_tasks'},
        {'text': '✏️Изменить статус задачи', 'callback_data': 'change_status'},
         {'text': 'Задачи для участника', 'callback_data': 'show_member_tasks'}
    ]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode='Markdown',
                          reply_markup=generate_inline_keyboard(buttons))


def edit_message_text(chat_id: int, message_id: Optional[int], text: str, reply_markup=None):
    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


def generate_inline_keyboard(buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['callback_data']))
    return markup


def show_back_button(chat_id, message_id, callback_data):
    buttons = [
        {'text': 'Назад', 'callback_data': callback_data}
    ]
    edit_message_text(chat_id, message_id, 'Выберите действие:', reply_markup=generate_inline_keyboard(buttons))

def edit_message_with_inline_keyboard(chat_id, message_id, text, buttons):
    markup = generate_inline_keyboard(buttons)
    edit_message_text(chat_id, message_id, text, reply_markup=markup)

bot.polling(none_stop=True)
