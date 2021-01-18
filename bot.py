#!/usr/bin/python3.6

import config
import telebot
from pyzabbix import ZabbixAPI
from suds.client import Client


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
            for item in items:
                if str(login_id) in item['name']:
                    if 'Signal level' in item['name']:
                        signal_level = item['lastvalue']
                        signal_level = round(float(signal_level), 1)
                    answer = f'''
Логин: {login_id} 
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


if __name__ == '__main__':
    bot.infinity_polling()
