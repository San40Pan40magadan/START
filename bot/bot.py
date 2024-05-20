import logging
import re
import paramiko
import os
import psycopg2

from psycopg2 import Error
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()

TOKEN = os.getenv("TOKEN")

RM_HOST = os.getenv("RM_HOST")
RM_PORT = os.getenv("RM_PORT")
RM_USER = os.getenv("RM_USER")
RM_PASSWORD = os.getenv("RM_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_PORT = os.getenv("DB_PORT")
DB_REPL_USER = os.getenv("DB_REPL_USER")
DB_REPL_PASSWORD = os.getenv("DB_REPL_PASSWORD")
DB_REPL_HOST = os.getenv("DB_REPL_HOST")
DB_REPL_PORT = os.getenv("DB_REPL_PORT")

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text(
        '/help - вызвать все команды\n/find_email - поиск email-адресов в тексте\n/find_phone_number - поиск номеров телефона в тексте\n/verify_password - проверка сложности пароля\n'
        '/get_release - О релизе\n/get_uname - Об архитектуры процессора, имени хоста системы и версии ядра. \n/get_uptime - О времени работы.\n'
        '/get_df - Сбор информации о состоянии файловой системы. \n/get_free - Сбор информации о состоянии оперативной памяти. \n/get_mpstat - Сбор информации о производительности системы.\n'
        '/get_w - Сбор информации о работающих в данной системе пользователях.\n/get_auths -  Последние 10 входов в систему. \n/get_critical - Последние 5 критических события.\n'
        '/get_ps - Сбор информации о запущенных процессах. \n/get_ss - Сбор информации об используемых портах.\n/get_apt_list - Сбор информации об установленных пакетах. \n/get_services - Сбор информации о запущенных сервисах. \n'
        '/get_repl_logs - Информация о запросе запуска, об остановке репликации, о готовности системы выполнить соединение. \n/get_emails - получить email-адреса из базы данных\n'
        '/get_phone_numbers - получить номера телефонов из базы данных\n')


def findPhoneNumberCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_Phone_Number'


def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска Email-адресов: ')

    return 'find_Email'


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки сложности, не вводите используемые пароли: ')

    return 'verify_Password'


def find_Phone_Number(update: Update, context):
    global PhoneNumberNew
    global phoneNumberList

    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|\+?7[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}|8[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}")  # формат +7/8XXXXXXXXXX, +7/8(XXX)XXXXXXX, +7/8 XXX XXX XX XX, 8 (XXX) XXX XX XX, 8-XXX-XXX-XX-XX

    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов

    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return  # Завершаем выполнение функции

    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{phoneNumberList[i]}\n'  # Записываем очередной номер

    PhoneNumberNew = phoneNumbers.split('\n')
    PhoneNumberNew.pop()

    update.message.reply_text(PhoneNumberNew)  # Отправляем сообщение пользователю
    update.message.reply_text('Записать найденные nелефонные номера в базу данных?\nДа, для записи. \nНет, для выхода.')
    return "get_Phone_Number"


def get_Phone_Number(update: Update, context):
    global PhoneNumberNew
    global phoneNumberList

    if update.message.text.strip() not in ('Да', 'Нет'):
        logging.info(f"{update.effective_user.full_name} entered not valid mode: {update.message.text}")

        user_response = update.message.text.upper()
        if user_response == 'ДА':
            update.message.reply_text(f"Вы выбрали запись номеров телефонов в базу:")
            for i in range(len(phoneNumberList)):
                update.message.reply_text(f"\n {PhoneNumberNew[i]}")
            connection = None
            try:
                connection = psycopg2.connect(user=DB_USER,
                                              password=DB_PASSWORD,
                                              host=DB_HOST,
                                              port=DB_PORT,
                                              database=DB_DATABASE)
                cursor = connection.cursor()
                for j in range(len(phoneNumberList)):
                    cursor.execute(f"INSERT INTO phonenumbers (phonenumber) VALUES ('{PhoneNumberNew[j]}');")
                    connection.commit()
                logging.info("Команда успешно выполнена")
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                update.message.reply_text('Телефон(ы) не сохранены в базе данных\nМожете повторить или выбрать другую команду')
                return ConversationHandler.END  # Завершаем работу обработчика диалога
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
            for p in range(len(phoneNumberList)):
                update.message.reply_text(f"Номер телефона: {PhoneNumberNew[p]} успешно добавлен в базу данных")
            update.message.reply_text('До встречи!')
            return ConversationHandler.END  # Завершаем работу обработчика диалога
        elif user_response == 'НЕТ':
            update.message.reply_text('Телефон(ы) не будет(-ут) сохранены в базе данных')
            return ConversationHandler.END  # Завершаем работу обработчика диалога
        else:
            update.message.reply_text(f"Пожалуйста, выберите, что хотите сделать с найденными телефонами, отправив Да или Нет")
        return "get_Phone_Number"

def find_Email(update: Update, context):
    global EmailsNew
    global findEmailList

    user_input = update.message.text  # Получаем текст, содержащий(или нет) Email-адреса

    findEmailRegex = re.compile(r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')  # формат xxxx@xxx.xx

    findEmailList = findEmailRegex.findall(user_input)  # Ищем Email-адреса

    if not findEmailList:  # Обрабатываем случай, когда Email-адресов нет
        update.message.reply_text('Email-адреса не найдены')
        update.message.reply_text('До встречи!')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    Emails = ''  # Создаем массив, в которую будем записывать Email-адреса
    for i in range(len(findEmailList)):
        Emails += f'{findEmailList[i]}\n'  # Записываем Email-адреса

    EmailsNew = Emails.split('\n')
    EmailsNew.pop()

    update.message.reply_text(EmailsNew)  # Отправляем сообщение пользователю
    update.message.reply_text('Записать найденные email-адреса в базу данных?\nДа, для записи. \nНет, для выхода.')
    return "get_email"


def get_email(update: Update, context):
    global EmailsNew
    global findEmailList

    if update.message.text.strip() not in ('Да', 'Нет'):
        logging.info(f"{update.effective_user.full_name} entered not valid mode: {update.message.text}")

        user_response = update.message.text.upper()
        if user_response == 'ДА':
            update.message.reply_text(f"Вы выбрали запись email-адресов в базу:")
            for i in range(len(findEmailList)):
                update.message.reply_text(f"\n {EmailsNew[i]}")
            connection = None
            try:
                connection = psycopg2.connect(user=DB_USER,
                                              password=DB_PASSWORD,
                                              host=DB_HOST,
                                              port=DB_PORT,
                                              database=DB_DATABASE)
                cursor = connection.cursor()
                for j in range(len(findEmailList)):
                    cursor.execute(f"INSERT INTO emails (email) VALUES ('{EmailsNew[j]}');")
                    connection.commit()
                logging.info("Команда успешно выполнена")
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
                update.message.reply_text('Email-адрес(а) не сохранены в базе данных\nМожете повторить или выбрать другую команду')
                return ConversationHandler.END  # Завершаем работу обработчика диалога
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
            for p in range(len(findEmailList)):
                update.message.reply_text(f"{EmailsNew[p]} успешно добавлен в базу данных")
            update.message.reply_text('До встречи!')
            return ConversationHandler.END  # Завершаем работу обработчика диалога
        elif user_response == 'НЕТ':
            update.message.reply_text('Email-адрес(а) не будет(-ут) сохранены в базе данных')
            return ConversationHandler.END  # Завершаем работу обработчика диалога
        else:
            update.message.reply_text(f"Пожалуйста, выберите, что хотите сделать с найденными email-адресами, отправив Да или Нет")
        return "get_email"

def verify_Password(update: Update, context):
    user_input = update.message.text  # Получаем пароль

    verifyPasswordRegex = re.compile(r'(?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{6,}')

    PassList = verifyPasswordRegex.findall(user_input)  # Получаем пароль

    if not PassList:  # Обрабатываем случай, когда пароль простой
        update.message.reply_text('Пароль простой')
        return  # Завершаем выполнение функции

    update.message.reply_text('Пароль сложный')  # Отправляем сообщение пользователю
    return ConversationHandler.END  # Завершаем работу обработчика диалога


def execute_ssh_command(hostname, port, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, port=port, username=username, password=password)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    client.close()
    return output


def get_release(update: Update, context):
    update.message.reply_text('Информация о релизе')
    command = "cat /etc/*release"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_uname(update: Update, context):
    update.message.reply_text('Информация об архитектуре процессора, имени хоста системы и версии ядра')
    command = "uname -a"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_uptime(update: Update, context):
    update.message.reply_text('Информация об времени работы')
    command = "uptime"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_df(update: Update, context):
    update.message.reply_text('Информация о состоянии файловой системы')
    command = "df -h"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_free(update: Update, context):
    update.message.reply_text('Информация о состоянии оперативной памяти')
    command = "free -h"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_mpstat(update: Update, context):
    update.message.reply_text('Информация о производительности системы')
    command = "mpstat"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_w(update: Update, context):
    update.message.reply_text('Информация о работающих в данной системе пользователях')
    command = "w"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_auths(update: Update, context):
    command = "last -n 10"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_critical(update: Update, context):
    update.message.reply_text('Информация о последних 5 критических событиях')
    command = "journalctl -p 2 -n 5"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_ps(update: Update, context):
    update.message.reply_text('Информация об запущенных процессах')
    command = "ps aux | head"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_ss(update: Update, context):
    update.message.reply_text('Информация об используемых портах')
    command = "ss -tunlp"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def getaptlistCommand(update: Update, context):
    update.message.reply_text(
        'all для получения информации о всех установленных пакетах\n или введите название сервиса для поиска информации об интересующем пакете')

    return 'get_apt_list'


def get_apt_list(update: Update, context):
    user_input = update.message.text
    if user_input == 'all':
        command = "dpkg --get-selections | grep -v deinstall | head -n 20"
    else:
        command = f"dpkg -l {user_input}"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)
    return ConversationHandler.END


def get_services(update: Update, context):
    update.message.reply_text('Информация о запущенных сервисах')
    command = "systemctl list-units --type=service --state=running | head -n 5"
    result = execute_ssh_command(RM_HOST, RM_PORT, RM_USER, RM_PASSWORD, command)
    update.message.reply_text(result)


def get_repl_logs(update: Update, context):
    update.message.reply_text(
        'Информация о запросе запуска, об остановке репликации, о готовности системы выполнить соединение')
    command = "cat /var/log/postgresql/postgresql.log | grep repl | tail -n 10"
    result = execute_ssh_command(DB_HOST, RM_PORT, DB_USER, DB_PASSWORD, command)
    update.message.reply_text(result)


def get_emails(update: Update, context):
    update.message.reply_text('Email-адреса из базы данных')
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,
                                      password=DB_PASSWORD,
                                      host=DB_HOST,
                                      port=DB_PORT,
                                      database=DB_DATABASE)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        for row in data:
            update.message.reply_text(row)  # Отправляем сообщение пользователю
    return ConversationHandler.END  # Завершаем работу обработчика диалога


def get_phone_numbers(update: Update, context):
    update.message.reply_text('Телефоны из базы данных')
    connection = None

    try:
        connection = psycopg2.connect(user=DB_USER,
                                      password=DB_PASSWORD,
                                      host=DB_HOST,
                                      port=DB_PORT,
                                      database=DB_DATABASE)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phonenumbers;")
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        for row in data:
            update.message.reply_text(row)  # Отправляем сообщение пользователю
    return ConversationHandler.END  # Завершаем работу обработчика диалога


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога

    convHandlerfindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_Email', findEmailCommand)],
        states={
            'find_Email': [MessageHandler(Filters.text & ~Filters.command, find_Email)],
            'get_email': [MessageHandler(Filters.text & ~Filters.command, get_email)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumber = ConversationHandler(
        entry_points=[CommandHandler('find_Phone_Number', findPhoneNumberCommand)],
        states={
            'find_Phone_Number': [MessageHandler(Filters.text & ~Filters.command, find_Phone_Number)],
            'get_Phone_Number': [MessageHandler(Filters.text & ~Filters.command, get_Phone_Number)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_Password', verifyPasswordCommand)],
        states={
            'verify_Password': [MessageHandler(Filters.text & ~Filters.command, verify_Password)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumber)
    dp.add_handler(convHandlerfindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    # Linux
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))

    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))

    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    convgetaptlist = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getaptlistCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )
    dp.add_handler(convgetaptlist)
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    # Регистрируем обработчик текстовых сообщений
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
