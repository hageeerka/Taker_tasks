import telebot
from telebot import types
from typing import Optional
import json
import os
import fnmatch
import requests
import datetime

TOKEN = '6414677588:AAEMOlh7rUvqcIzAVMuzPi-GADWp16kObHM'
bot = telebot.TeleBot(TOKEN)
temp_data = {}  # словарь {id чата: username руководителя}
all_tasks = {}  # словарь {id задачи:{информация о задаче}}
my_team = {}  # словарь {id участника: {информация об участнике}}
task_id = None  # глобальная переменная id чата
member_id = None  # глобальная переменная id участника


@bot.message_handler(commands=['menu'])  # при отправке пользователем сообщения '/menu'
def data_recovery(message):
    '''
    Считывает id чата и создаёт пустые словари в словарях temp_data, all_tasks,
    my_team, доступные по ключу, равному id чата и загружает информацию из локальной папки в эти словари.
    Отправляет собщение с кнопками Главного меню
    :param message: сообщение пользоваеля, содержащее команду '/menu'
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    temp_data[chat_id] = {}
    all_tasks[chat_id] = {}
    my_team[chat_id] = {}
    handle_load_command(chat_id)
    show_menu(chat_id)


@bot.message_handler(commands=['start'])  # при отправке пользователем сообщения '/start'
def start_message(message):
    '''
    Считывает id чата и создаёт пустые словари в словарях temp_data, all_tasks,
    my_team, доступные по ключу, равному id чата и загружает информацию из локальной папки в эти словари
    Отправляет текст с приветствием и кнопкой добавления руководителя проекта.
    :param message: сообщение пользоваеля, содержащее команду '/start'
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    text = f'Привет!👋🏼\nЯ Чат-бот Трекер задач, готов помочь вам с организацией работы над проектом. \n' \
           'Вместе мы сможем эффективно достигать поставленных целей. \n' \
           '*Для начала назначьте должность Руководителя.* '
    buttons = [types.InlineKeyboardButton('▶️Добавить руководителя', callback_data='add_director')]

    temp_data[chat_id] = {}
    all_tasks[chat_id] = {}
    my_team[chat_id] = {}
    handle_load_command(chat_id)

    bot.send_message(chat_id, text, reply_markup=types.InlineKeyboardMarkup().add(*buttons), parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    '''
    Функция, которая обрабатывает нажатия на все кнопки
    :param call: объект с информацией о нажатии кнопки
    :type call: <class 'telebot.types.CallbackQuery'>
    '''
    chat_id = call.message.chat.id  # id чата, с которым происходит работа
    message_id = call.message.message_id  # id сообщения ?
    data = call.data  # ?
    # При нажатии на кнопку 'Добавить руководителя' создаётся ключ "director_id" с пустым значенем, начинается заполнение информации о руководителе
    if data == 'add_director':
        temp_data[chat_id][chat_id] = {"director_id": None}
        bot.send_message(chat_id, "Напишите @username руководителя")
        bot.register_next_step_handler(call.message, set_director)
    # При нажатии кнопки 'Создать задачу' переменная task_id принимает значение следущей по счёту задачи и создаёт словарь
    # с информацией о задаче в словаре all_tasks  под ключём task_id, начинается этого словаря с добавления названия задачи
    if data == 'add_task':
        global task_id
        task_id = 'task_' + str(len(all_tasks[chat_id]) + 1)
        all_tasks[chat_id][task_id] = {"name": None, 'description': None, 'deadline': None, 'responsible': None,
                                       'priority': None, 'timer': None}
        bot.send_message(chat_id, "Напишите название задачи")
        bot.register_next_step_handler(call.message, set_name)
    # При нажатии кнопки 'Редактировать задачу' выводится сообщение с информацией о всех задачах
    # выводится сообщение с кнопками с номерами задач по порядку и кнопкой вернуться назад
    if data == 'edit_task':

        if len(all_tasks[chat_id]) != 0:
            text = '*Список задач*:\n'
            for i in range(len(all_tasks[chat_id])):
                task_id = 'task_' + str(i + 1)
                update_timer(chat_id)
                text += f"*_Задача № {i + 1}_*\n" \
                        f"*Название*: {all_tasks[chat_id][task_id]['name']}\n" \
                        f"*Описание*: {all_tasks[chat_id][task_id]['description']}\n" \
                        f"*Дедлайн*: {all_tasks[chat_id][task_id]['deadline']}\n" \
                        f"*Приоритет*: {all_tasks[chat_id][task_id]['priority']}\n" \
                        f"*До дедлайна осталось*: {all_tasks[chat_id][task_id]['timer']}\n"
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
            buttons = []
            for i in range(1, len(all_tasks[chat_id]) + 1):
                buttons.append({'text': str(i), 'callback_data': f'edit_task_{i}'})
            buttons.append({'text': '🔙Вернуться назад', 'callback_data': 'menu'})
            text = 'Выберите задачу, которую хотите изменить'
            send_message_with_inline_keyboard(chat_id, text, buttons)
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
    if data == 'all_tasks':
        show_all_tasks(message_id, chat_id)

    if data.startswith('show_member_tasks'):
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(my_team[chat_id]['member_' + str(i)]['username'],
                                              callback_data=f'show_tasks_for_member_{i}') for i in
                   range(1, len(my_team[chat_id]) + 1)]
        markup.add(*buttons)
        edit_message_text(chat_id, message_id, text='Выбери участника, для которого хочешь посмотреть задачи',
                          reply_markup=markup)

    if data.startswith('show_tasks_for_member_'):
        global member_id
        member_id = 'member_' + data[-1]
        tasks = []
        buttons = []
        text = 'Выберите задачу, информация о которой вам интересна. Задачи расположены в порядке приоритета от наиболее важных к наименее важным.'
        for task_id in all_tasks[chat_id]:
            if all_tasks[chat_id][task_id]['responsible'] is not None:
                if my_team[chat_id][member_id]['username'] in all_tasks[chat_id][task_id]['responsible']:
                    tasks.append(task_id)
        for num_priority in range(1, 6):
            for task_id in tasks:
                if num_priority == int(all_tasks[chat_id][task_id]['priority']):
                    buttons.append({'text': all_tasks[chat_id][task_id]['name'],
                                    'callback_data': f'show_task_{task_id[-1]}_for_member_{member_id[-1]}'})
        edit_message_with_inline_keyboard(chat_id, message_id, text, buttons)

    if data.startswith('show_task_'):
        task_id = 'task_' + data[10]
        update_timer(chat_id)
        member_id = 'member_' + data[-1]
        text = f"Задача № {task_id[-1]}\n" \
               f"Название:{all_tasks[chat_id][task_id]['name']}\n" \
               f"Описание: {all_tasks[chat_id][task_id]['description']}\n" \
               f"Дедлайн: {all_tasks[chat_id][task_id]['deadline']}\n" \
               f"Приоритет: {all_tasks[chat_id][task_id]['priority']}\n" \
               f"До дедлайна осталось: {all_tasks[chat_id][task_id]['timer']}\n"
        buttons = [
            {'text': '🔙Выбрать другую задачу', 'callback_data': f'show_tasks_for_member_{task_id[-1]}'},
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        edit_message_with_inline_keyboard(chat_id, message_id, text, buttons)

    if data == 'return_menu':
        show_menu(chat_id)

    if data == 'return_all_tasks':
        show_all_tasks(message_id, chat_id)

    if data == 'completed_tasks':
        completed_tasks = [task_id for task_id, task_info in all_tasks[chat_id].items() if
                           task_info.get('completed', False)]
        if not completed_tasks:
            text = 'Нет выполненных задач.'
        else:
            text = 'Выполненные задачи:\n'
            for i, task_id in enumerate(completed_tasks, start=1):
                text += f"{i}. {all_tasks[chat_id][task_id]['name']}\n"
        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data == 'uncompleted_tasks':
        uncompleted_tasks = [task_id for task_id, task_info in all_tasks[chat_id].items() if
                             not task_info.get('completed', False)]
        if not uncompleted_tasks:
            text = 'Нет невыполненных задач.'
        else:
            text = 'Невыполненные задачи:\n'
            for i, task_id in enumerate(uncompleted_tasks, start=1):
                text += f"{i}. {all_tasks[chat_id][task_id]['name']}\n"
        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data == 'change_status':
        text = 'Выберите задачу для изменения статуса:'
        buttons = [
            {'text': f'{i + 1}. {task_info["name"]}', 'callback_data': f'change_status_{task_id}'}
            for i, (task_id, task_info) in enumerate(all_tasks[chat_id].items())
        ]
        buttons.append({'text': 'Назад', 'callback_data': 'return_all_tasks'})
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))

    if data.startswith('change_status_'):
        task_id_to_change = data.replace('change_status_', '')
        if task_id_to_change in all_tasks[chat_id]:
            task_info = all_tasks[chat_id][task_id_to_change]
            current_status = task_info.get('completed', False)
            new_status = not current_status
            task_info['completed'] = new_status
            text = f"Статус задачи изменен на {'Выполнена' if new_status else 'Не выполнена'}."
        else:
            text = "Задача не найдена."

        buttons = [{'text': 'Назад', 'callback_data': 'return_all_tasks'}]
        edit_message_text(chat_id, message_id, text, reply_markup=generate_inline_keyboard(buttons))


    if data == 'menu':
        show_menu(chat_id)
    if data.startswith('priority'):
        all_tasks[chat_id][task_id]['priority'] = int(data.split('_')[1])
        update_timer(chat_id)
        if len(my_team[chat_id]) == 0:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'add_member'}
            ]
        else:
            buttons = [
                {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
            ]
        text = f"Ваша задача создана, проверьте информацию.\n" \
               f"🔸Название: {all_tasks[chat_id][task_id]['name']}\n" \
               f"🔸Описание: {all_tasks[chat_id][task_id]['description']}\n" \
               f"🔸Дедлайн: {all_tasks[chat_id][task_id]['deadline']}\n" \
               f"🔸Приоритет: {all_tasks[chat_id][task_id]['priority']}\n" \
               f"🔸До дедлайна осталось: {all_tasks[chat_id][task_id]['timer']}\n" \
               "P.S. Изменить задачу вы можете в разделе 'Главное меню'"
        send_message_with_inline_keyboard(chat_id, text, buttons=buttons)

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
            all_tasks[chat_id]['task_' + str(i)] = all_tasks['task_' + str(i + 1)]
        del all_tasks[chat_id]['task_' + str(len(all_tasks))]
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Эта задача была удалена из списка.'
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'add_member':
        additional_text = ''
        if len(my_team[chat_id]) == 0:
            additional_text = 'Теперь вам необходимо добавить первого участника в команду. '
        member_id = 'member_' + str(len(my_team[chat_id]) + 1)
        my_team[chat_id][member_id] = {"username": None, 'firstname': None, 'lastname': None, 'role': None}
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
        for i in range(member_id_number, len(my_team[chat_id])):
            my_team[chat_id]['member_' + str(i)] = my_team[chat_id]['member_' + str(i + 1)]
        del my_team[chat_id]['member_' + str(len(my_team[chat_id]))]
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Этот участник был удалён из команды.'
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'delete_member':
        if len(my_team[chat_id]) != 0:
            markup = types.InlineKeyboardMarkup()
            buttons = [
                types.InlineKeyboardButton(my_team[chat_id]['member_' + str(i)]['username'],
                                           callback_data=f'del_member_{i}') for
                i in
                range(1, len(my_team[chat_id]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите участника, которого хотите удалить из команды.',
                             reply_markup=markup)
    if data.startswith('add_responsible_member_'):
        all_tasks[chat_id][f'task_{data[23]}']['responsible'] = 'member_' + str(data[-1])
        buttons = [
            {'text': "Вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = 'Отлично, участник закреплён за задачей!'
        send_message_with_inline_keyboard(chat_id, text, buttons)

    if data.startswith('add_responsible_for_task_'):
        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton(my_team[chat_id]['member_' + str(i)]['username'],
                                       callback_data=f'add_responsible_member_{i}_for_task_{str(data[-1])}') for
            i in
            range(1, len(my_team[chat_id]) + 1)]
        markup.add(*buttons)
        bot.send_message(chat_id, text='Выберите участника, которого хотите закрепить за задачей.',
                         reply_markup=markup)
    if data == 'assign_roles':
        if len(all_tasks[chat_id]) != 0:
            text = '*Список задач*:\n'
            for i in range(len(all_tasks[chat_id])):
                task_id = 'task_' + str(i + 1)
                update_timer(chat_id)
                text += f"_Задача № {i + 1}_\n" \
                        f"Название:{all_tasks[chat_id][task_id]['name']}\n" \
                        f"Описание: {all_tasks[chat_id][task_id]['description']}\n" \
                        f"Дедлайн: {all_tasks[chat_id][task_id]['deadline']}\n" \
                        f"Приоритет: {all_tasks[chat_id][task_id]['priority']}\n" \
                        f"До дедлайна осталось: {all_tasks[chat_id][task_id]['timer']}\n"
            bot.send_message(chat_id, text=text, parse_mode='Markdown')
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'assign_members_to_task_{i}') for i in
                       range(1, len(all_tasks[chat_id]) + 1)]
            markup.add(*buttons)
            bot.send_message(chat_id, text='Выберите задачу, за которой хотите закрепить участника',
                             reply_markup=markup)
    if data.startswith('assign_members_to_task_'):
        all_tasks[chat_id]['task_' + data[-1]]['responsible'] = None
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(my_team[chat_id]['member_' + str(i)]['username'],
                                              callback_data=f'assign_member_{i}_for_task_{data[-1]}') for i in
                   range(1, len(my_team[chat_id]) + 1)]
        buttons += {types.InlineKeyboardButton('Готово!',
                                               callback_data=f'ready_to_assign')}
        markup.add(*buttons)
        bot.send_message(chat_id,
                         text='Нажмите на @username всех участников, которые будет закреплены за задачей. Затем нажмите кнопку "Готово!"',
                         reply_markup=markup)
    if data.startswith('assign_member_'):
        task_id = 'task_' + data[-1]
        if all_tasks[chat_id][task_id]['responsible'] is None:
            all_tasks[chat_id][task_id]['responsible'] = [my_team[chat_id]['member_' + data[14]]['username']]
        else:
            all_tasks[chat_id][task_id]['responsible'] += [my_team[chat_id]['member_' + data[14]]['username']]
    if data == 'ready_to_assign':
        text = f"Отлично, теперь за задачей под названием {all_tasks[chat_id][task_id]['name']} закреплен(ы) участник(и) с @username {all_tasks[chat_id][task_id]['responsible']}"
        buttons = [
            {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        send_message_with_inline_keyboard(chat_id, text, buttons)
    if data == 'show_team':
        if len(my_team[chat_id]) == 0:
            text = 'На данный момент ваша команда не сформирована, добавьте участников, чтобы исправить это.'
        else:
            text = "Список участников:\n"
            for i in range(len(my_team[chat_id])):
                show_member_id = 'member_' + str(i + 1)
                text += f"Участник № {i + 1}\n" \
                        f"🔸@username: {my_team[chat_id][show_member_id]['username']}\n" \
                        f"🔸Имя: {my_team[chat_id][show_member_id]['firstname']}\n" \
                        f"🔸Фамилия: {my_team[chat_id][show_member_id]['lastname']}\n" \
                        f"🔸Роль: {my_team[chat_id][show_member_id]['role']}\n"
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
        if len(my_team[chat_id]) != 0:
            text = 'Список участников:\n'
            for i in range(len(my_team[chat_id])):
                show_member_id = 'member_' + str(i + 1)
                text += f"Участник № {i + 1}\n" \
                        f"🔸@username: {my_team[chat_id][show_member_id]['username']}\n" \
                        f"🔸Имя: {my_team[chat_id][show_member_id]['firstname']}\n" \
                        f"🔸Фамилия: {my_team[chat_id][show_member_id]['lastname']}\n" \
                        f"🔸Роль: {my_team[chat_id][show_member_id]['role']}\n"
            bot.send_message(chat_id, text=text)
            markup = types.InlineKeyboardMarkup()
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f'edit_member_{i}') for i in
                       range(1, len(my_team[chat_id]) + 1)]
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


def save_my_team(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/m{chat_id}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(my_team[chat_id], file, ensure_ascii=False)


def load_my_team(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/m{chat_id}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            my_team[chat_id].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


def save_all_tasks(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/a{chat_id}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(all_tasks[chat_id], file, ensure_ascii=False)


def load_all_tasks(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/a{chat_id}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            all_tasks[chat_id].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


def save_temp_data(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/t{chat_id}.json"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(temp_data[chat_id], file, ensure_ascii=False)


def load_temp_data(chat_id):
    file_path = f"C:/Users/Диана/PycharmProjects/pythonProject/Новая папка/t{chat_id}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            temp_data[chat_id].update(data)
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")


def handle_save_command(chat_id):
    save_my_team(chat_id)
    save_temp_data(chat_id)
    save_all_tasks(chat_id)


def handle_load_command(chat_id):
    load_my_team(chat_id)
    load_temp_data(chat_id)
    load_all_tasks(chat_id)


def send_message_with_inline_keyboard(chat_id, text, buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['callback_data']))
    bot.send_message(chat_id, text, reply_markup=markup)


def neuroask(message):
    chat_id = message.chat.id
    url = "https://llm.api.cloud.yandex.net/llm/v1alpha/chat"
    data = {
        "model": "general",
        "generationOptions": {
            "partialResults": True,
            "temperature": 0.4,
            "maxTokens": 400
        },
        "messages": [
            {
                "role": "ai.languageModels.user",
                "text": message.text.strip()
            }
        ],
        "instructionText": "ты умная нейросеть и помогаешь людям решать рабочие проблемы",
    }
    headers = {"Authorization": f'Api-Key {"AQVNwWtHH04wz-RRaNbCS4DH1cMfJdp67NmvF4e0"}',
               }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        first_ans = json.loads(response.text.split('}\n')[-2] + '}')
        bot.send_message(chat_id, first_ans['result']['message']['text'])
    else:
        buttons = [
            {'text': 'Назад', 'callback_data': 'menu'}
        ]
        text = 'Извините, что-то пошло не так'
        send_message_with_inline_keyboard(chat_id, text, buttons)


def show_menu(chat_id):
    '''
    Присылает сообщение главного меню с кнопками
    :param chat_id: id чата, куда боту нужно прислать сообщение
    :type chat_id: int
    '''
    buttons = [
        {'text': '➕Создать новую задачу', 'callback_data': 'add_task'},
        {'text': '📝Распределить участников по задачам', 'callback_data': 'assign_roles'},
        {'text': '🔝Моя команда', 'callback_data': 'team'},
        {'text': '✏️Редактировать задачу', 'callback_data': 'edit_task'},
        {'text': '📚Ваши задачи', 'callback_data': 'all_tasks'},
        {'text': '💡Попросить совет', 'callback_data': 'gpt'}
    ]
    text = 'Отлично! Теперь вы можете распределить роли и поставить задачи.'
    send_message_with_inline_keyboard(chat_id, text, buttons)
    handle_save_command(chat_id)


def set_director(message):
    '''
    Проверяет введённое пользователем сообщение на соответствие формату username,
    добавляет username руководителя в словарь temp_data и локально сохраняет его;
    затем перенаправляет пользователя к созданию задачи.
    :param message: сообщение пользоваеля, содержащее username руководителя
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if chat_id in temp_data[chat_id] and temp_data[chat_id][chat_id]["director_id"] is None:
        username = message.text.strip()
        if username.startswith("@"):
            temp_data[chat_id][chat_id]["director_id"] = username
            buttons = [
                {'text': '➕Создать новую задачу', 'callback_data': 'add_task'}
            ]
            text = 'Отлично! Теперь вам необходимо создать первую задачу.'
            send_message_with_inline_keyboard(chat_id, text, buttons)

        else:
            bot.send_message(chat_id, '*Пожалуйста, напишите @username в верном формате.*', parse_mode='Markdown')
            bot.register_next_step_handler(message, set_director)
        handle_save_command(chat_id)


def show_change_of_task(chat_id):
    '''
    Выводит в чат сообщение со всей информацией о задаче с id = task_id и кнопкой возврата в главное меню
    или добавления первого участника в команде в случае пустого словаря со списком участников команд
    :param chat_id: id чата, куда боту нужно прислать сообщение
    :type chat_id: int
    '''
    update_timer(chat_id)
    if len(my_team[chat_id]) == 0:
        buttons = [
            {'text': '🟢Всё верно, вернуться добавить первого участника', 'callback_data': 'add_member'}
        ]
    else:
        buttons = [
            {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
        ]
    text = f"Информация о задаче изменена.\n" \
           f"🔸Название: {all_tasks[chat_id][task_id]['name']}\n" \
           f"🔸Описание: {all_tasks[chat_id][task_id]['description']}\n" \
           f"🔸Дедлайн: {all_tasks[chat_id][task_id]['deadline']}\n" \
           f"🔸Приоритет: {all_tasks[chat_id][task_id]['priority']}\n" \
           f"🔸До дедлайна осталось {all_tasks[chat_id][task_id]['timer']}\n" \
           "P.S. изменить задачу вы можете в разделе 'Главное меню'"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def update_timer(chat_id):
    deadline = datetime.datetime.strptime(all_tasks[chat_id][task_id]['deadline'], "%Y-%m-%d %H:%M")
    remaining_time = deadline - datetime.datetime.now()
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days = remaining_time.days
    timer_string = "{:02} day(s) {:02} hour(s) {:02} minute(s)".format(days, int(hours), int(minutes))
    all_tasks[chat_id][task_id]['timer'] = timer_string
    if deadline < datetime.datetime.now():
        all_tasks[chat_id][task_id]['timer'] = "{:02} day(s) {:02} hour(s) {:02} minute(s) ".format(0, 0, 0)


def show_change_of_member(chat_id):
    '''
    Выводит в чат сообщение со всей информацией об участнике с id = member_id и кнопкой возврата в главное меню
    :param chat_id: id чата, куда боту нужно прислать сообщение
    :type chat_id: int
    '''
    buttons = [
        {'text': '🟢Всё верно, вернуться в главное меню', 'callback_data': 'menu'}
    ]
    text = f"Информация об участнике изменена.\n" \
           f"🔸@username: {my_team[chat_id][member_id]['username']}\n" \
           f"🔸Имя: {my_team[chat_id][member_id]['firstname']}\n" \
           f"🔸Фамилия: {my_team[chat_id][member_id]['lastname']}\n" \
           f"🔸Роль: {my_team[chat_id][member_id]['role']}\n" \
           "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
    send_message_with_inline_keyboard(chat_id, text, buttons)


def set_name(message):
    '''
    Добавляет название задачи с id = task_id в словарь all_tasks,
    перенаправляет пользователя к созданию описания задачи
    :param message: сообщение пользоваеля, содержащее название задачи
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    all_tasks[chat_id][task_id]['name'] = message.text.strip()
    bot.send_message(chat_id, 'Напишите описание задачи')
    bot.register_next_step_handler(message, set_description)
    handle_save_command(chat_id)


def edit_name(message):
    '''
    Изменяет название задачи с id = task_id и сохраняет его в словарь all_tasks,
    затем выводит сообщение с обновлённой информацией о задаче
    :param message: сообщение пользоваеля, содержащее название задачи
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    all_tasks[chat_id][task_id]['name'] = message.text.strip()
    show_change_of_task(chat_id)


def set_description(message):
    '''
    Добавляет описание задачи с id = task_id в словарь all_tasks,
    перенаправляет пользователя установке дедлайна текущей задачи
    :param message: сообщение пользоваеля, содержащее описание задачи
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    all_tasks[chat_id][task_id]['description'] = message.text.strip()
    bot.send_message(chat_id,
                     'Установите дедлайн. Укажите дату и время в формате: year-month-day hours:minutes, например, 2023-12-31 12:00')
    bot.register_next_step_handler(message, set_deadline)


def edit_description(message):
    '''
    Изменяет описание задачи с id = task_id и сохраняет его в словарь all_tasks,
    затем выводит сообщение с обновлённой информацией о задаче
    :param message: сообщение пользоваеля, содержащее описание задачи
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    all_tasks[chat_id][task_id]['description'] = message.text.strip()
    show_change_of_task(chat_id)


def set_deadline(message):
    chat_id = message.chat.id
    if fnmatch.fnmatch(message.text, "????-??-?? ??:??"):
        try:
            # Пытаемся преобразовать введенную дату в объект datetime
            deadline = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M")

            # Валидация дедлайна
            if deadline < datetime.datetime.now():
                bot.send_message(chat_id, "Указанный дедлайн уже прошел.")
            else:
                # Присваиваем дедлайн задаче
                all_tasks[chat_id][task_id]['deadline'] = deadline.strftime("%Y-%m-%d %H:%M")

                # Отправляем сообщение с выбором приоритета
                buttons = [types.InlineKeyboardButton(str(i), callback_data=f'priority_{i}') for i in range(1, 6)]
                markup = types.InlineKeyboardMarkup()
                markup.add(*buttons)
                bot.send_message(chat_id, text='Выберите приоритет задачи.', reply_markup=markup)
        except ValueError:
            new_message = bot.send_message(chat_id,
                                           '*Пожалуйста, укажите дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ.*',
                                           parse_mode='Markdown')
            bot.register_next_step_handler(new_message, set_deadline)
    else:
        new_message = bot.send_message(chat_id,
                                       '*Пожалуйста, укажите дедлайн формате year-month-date hours:minutes.*',
                                       parse_mode='Markdown')
        bot.register_next_step_handler(new_message, set_deadline)


def edit_deadline(message):
    '''
    Проверяет сообщение пользоваеля на соответствие формату даты,
    изменяет дедлайн задачи с id = task_id и сохраняет его в словарь all_tasks,
    затем выводит сообщение с обновлённой информацией о задаче
    :param message: сообщение пользоваеля, содержащее дедлайн задачи
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    all_tasks[chat_id][task_id]['deadline'] = message.text.strip()

    if fnmatch.fnmatch(message.text, "????-??-?? ??:??"):
        try:
            show_change_of_task(chat_id)
        except ValueError:
            new_message = bot.send_message(chat_id,
                                           '*Пожалуйста, укажите дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ.*',
                                           parse_mode='Markdown')
            bot.register_next_step_handler(new_message, edit_deadline)
    else:
        new_message = bot.send_message(chat_id, '*Пожалуйста, укажите дедлайн формате date.month.year hours:minutes.*',
                                       parse_mode='Markdown')
        bot.register_next_step_handler(new_message, edit_deadline)


def set_username(message):
    '''
    Проверяет сообщение пользователя на соответствие формату username,
    добавляет username участника команды с id = member_id в словарь my_team,
    перенаправляет пользователя к заполнению имени участника
    :param message: сообщение пользоваеля, содержащее username участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if my_team[chat_id][member_id]['username'] is None:
        my_team[chat_id][member_id]['username'] = message.text.strip()
        if my_team[chat_id][member_id]['username'].startswith('@'):
            bot.send_message(chat_id, 'Напишите имя участника')
            bot.register_next_step_handler(message, set_firstname)
        else:
            my_team[chat_id][member_id]['username'] = None
            bot.send_message(chat_id, '*Пожалуйста, введите @username в верном формате.*', parse_mode='Markdown')
            bot.register_next_step_handler(message, set_username)


def edit_username(message):
    '''
    Проверяет сообщение пользоваеля на соответствие формату username,
    изменяет username участника с id = member_id и сохраняет его в словарь my_team,
    затем выводит сообщение с обновлённой информацией об участнике
    :param message: сообщение пользоваеля, содержащее username участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if message.text.startswith('@'):
        my_team[chat_id][member_id]['username'] = message.text.strip()  #
        show_change_of_member(chat_id)
    else:
        bot.send_message(chat_id, '*Пожалуйста, введите @username в верном формате.*', parse_mode='Markdown')
        bot.register_next_step_handler(message, edit_username)


def set_firstname(message):
    '''
    Добавляет имя участника команды с id = member_id в словарь my_team,
    перенаправляет пользователя к заполнению фамилии участника
    :param message: сообщение пользоваеля, содержащее имя участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if my_team[chat_id][member_id]['username'] is not None and my_team[chat_id][member_id]['firstname'] is None:
        my_team[chat_id][member_id]['firstname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите фамилию участника')
        bot.register_next_step_handler(message, set_lastname)


def edit_firstname(message):
    '''
    Изменяет имя участника с id = member_id и сохраняет его в словарь my_team,
    затем выводит сообщение с обновлённой информацией об участнике
    :param message: сообщение пользоваеля, содержащее username участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    my_team[chat_id][member_id]['firstname'] = message.text.strip()
    show_change_of_member(chat_id)


def set_lastname(message):
    '''
    Добавляет фамилию участника команды с id = member_id в словарь my_team,
    перенаправляет пользователя к заполнению роли участника
    :param message: сообщение пользоваеля, содержащее имя участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if my_team[chat_id][member_id]['username'] is not None and my_team[chat_id][member_id][
        'firstname'] is not None and \
            my_team[chat_id][member_id]['lastname'] is None:
        my_team[chat_id][member_id]['lastname'] = message.text.strip()
        bot.send_message(chat_id, 'Напишите роль участника')
        bot.register_next_step_handler(message, set_role)


def edit_lastname(message):
    '''
    Изменяет фамилию участника с id = member_id и сохраняет его в словарь my_team,
    затем выводит сообщение с обновлённой информацией об участнике
    :param message: сообщение пользоваеля, содержащее username участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    my_team[chat_id][member_id]['lastname'] = message.text.strip()
    show_change_of_member(chat_id)


def set_role(message):
    '''
    Добавляет роль участника команды с id = member_id в словарь my_team,
    Выводит сообщение с обновлённой информацией об участнике и кнопкой, возвращающей в главное меню
    :param message: сообщение пользоваеля, содержащее имя участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    if my_team[chat_id][member_id]['username'] is not None and my_team[chat_id][member_id][
        'firstname'] is not None and \
            my_team[chat_id][member_id]['lastname'] is not None and my_team[chat_id][member_id]['role'] is None:
        my_team[chat_id][member_id]['role'] = message.text.strip()
        buttons = [
            {'text': "Всё верно, вернуться в Главное меню", 'callback_data': 'menu'}
        ]
        text = f"Участник создан, проверьте информацию.\n" \
               f"🔸@username: {my_team[chat_id][member_id]['username']}\n" \
               f"🔸Имя: {my_team[chat_id][member_id]['firstname']}\n" \
               f"🔸Фамилия: {my_team[chat_id][member_id]['lastname']}\n" \
               f"🔸Роль: {my_team[chat_id][member_id]['role']}\n" \
               "P.S. изменить информацию можно в разделе 'Моя команда'.\n"
        send_message_with_inline_keyboard(chat_id, text, buttons)


def edit_role(message):
    '''
    Изменяет роль участника с id = member_id и сохраняет его в словарь my_team,
    затем выводит сообщение с обновлённой информацией об участнике
    :param message: сообщение пользоваеля, содержащее username участника
    :type message: <class 'telebot.types.Message'>
    '''
    chat_id = message.chat.id
    my_team[chat_id][member_id]['role'] = message.text.strip()
    show_change_of_member(chat_id)
    handle_save_command(chat_id)


def show_all_tasks(message_id, chat_id):
    text = '*Все задачи:*\n'
    for i, task_id in enumerate(all_tasks[chat_id].keys(), start=1):
        task_info = all_tasks[chat_id][task_id]
        status = "_Выполнена_" if task_info.get('completed', False) else "_Не выполнена_"
        text += f"{i}. {task_info['name']} - {status}\n"
    buttons = [
        {'text': '🔙Вернуться в Главное меню', 'callback_data': 'return_menu'},
        {'text': '❌Невыполненные задачи', 'callback_data': 'uncompleted_tasks'},
        {'text': '✅Выполненные задачи', 'callback_data': 'completed_tasks'},
        {'text': '✏️Изменить статус задачи', 'callback_data': 'change_status'},
        {'text': '👤Задачи для участника', 'callback_data': 'show_member_tasks'}
    ]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode='Markdown',
                          reply_markup=generate_inline_keyboard(buttons))
    handle_save_command(chat_id)


def edit_message_text(chat_id: int, message_id: Optional[int], text: str, reply_markup=None):
    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    handle_save_command(chat_id)


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
    handle_save_command(chat_id)


def edit_message_with_inline_keyboard(chat_id, message_id, text, buttons):
    markup = generate_inline_keyboard(buttons)
    edit_message_text(chat_id, message_id, text, reply_markup=markup)


bot.polling(none_stop=True)
