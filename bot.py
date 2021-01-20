#!/usr/bin/python3.6

import config
import telebot
from pyzabbix import ZabbixAPI
from suds.client import Client
from reconfig_onu import reconfig_onu


bot = telebot.TeleBot(config.token)
white_list = config.white_list


def user_info(message):
    answer = "Данные отсутствуют"
    login_id = message.text
    endpoint = config.wsdl_url
    service_url = config.service_url
    client = Client(endpoint, faults=False)
    client.set_options(location=service_url)
    manager = client.service.Login(config.billing_login, config.billing_password)

    users = client.service.getVgroups(flt={'login': login_id})
    if len(users[1]) > 0:
        try:
            port = client.service.getPorts(flt={'vgid': users[1][0]['vgid']})
            device = client.service.getDevice(id=port[1][0]['deviceid'])
            devicename = device[1][0]['device']['devicename']
            zb = ZabbixAPI('http://zabbix.opti', user=config.zabbix_login, password=config.zabbix_password)
            items = zb.item.get(host=devicename, output=['itemid', 'name', 'lastvalue'])
            signal_level = 'Данные отсутствуют'
            port_status = 'Данные отсутствуют'
            for item in items:
                if str(login_id) in item['name']:
                    if 'status' in item['name']:
                        print()
                        if int(item['lastvalue']) == 1:
                            port_status = 'Up'
                        else:
                            port_status = 'Down'
            for item in items:
                if str(login_id) in item['name']:
                    if 'Signal level' in item['name']:
                        if port_status == 'Down':
                            signal_level = 'Данные отсутствуют'
                        elif port_status == 'Up':
                            signal_level = item['lastvalue']
                            signal_level = round(float(signal_level), 1)
            answer = f'''
Логин: {login_id}
Статус порта: {port_status}
Уровень сигнала: {signal_level}
'''
        except IndexError:
            answer = "Данные отсутствуют"
    else:
        answer = "Пользователь не найден"
    bot.send_message(message.chat.id, answer)


@bot.message_handler(func=lambda message: message.chat.id not in white_list)
def access_denied(message):
    print(message)
    bot.send_message(message.chat.id, 'Доступ закрыт')


@bot.message_handler(content_types=['text'])
def get_message(message):
    if message.text.startswith('100'):
        user_info(message)
    elif message.text.startswith('200'):
        user_info(message)
    elif "ON" in message.text:
        user_info(message)
    elif message.text.startswith('GON'):
        user_info(message)
    elif message.text == '/help':
        help_answer = '''
- /reconfig - замена клиентского ONU
- Чтобы посмотреть уровень затуханий введите логин абонента
        '''
        bot.send_message(message.chat.id, help_answer)
    elif message.text == '/reconfig':
        reconfig_message = '''
- Для продолжения настройки введите логин абонента и дождитесь завершения настройки;
- Для прекращения настройки введите /stop.
        '''
        bot.send_message(message.chat.id, reconfig_message)
        bot.register_next_step_handler(message, config_onu)


def config_onu(message):
    try:
        if message.text == '/stop':
            bot.register_next_step_handler(message, get_message)
            bot.send_message(message.chat.id, 'Замена клиентского ONU остановлена')
        else:
            bot.send_message(message.chat.id, reconfig_onu(message.text))
    except IndexError:
        bot.register_next_step_handler(message, get_message)
        bot.send_message(message.chat.id, 'Пользователь не найден, настройка прекращена')


if __name__ == '__main__':
    bot.infinity_polling()
