from suds.client import Client


def userinfo(message):

    session_status = 'Нет активной сессии'

    login_id = message.text
    endpoint = "http://172.16.89.4:8088/billing/phpclient/admin/soap/api3.wsdl"
    service_url = 'http://172.16.89.4:34012'
    client = Client(endpoint, faults=False)
    client.set_options(location=service_url)
    manager = client.service.Login('userinfo', ')@6D2f78')

    users = client.service.getVgroups(flt={'login': login_id})
    user = users[1][0]
    account = client.service.getAccount(id=user['uid'])
    account = account[1][0]
    tarif_info = client.service.getTarif(id=user['tarid'])
    tarif_info = tarif_info[1][0]
    block_id = user['blocked']
    abonent_name = user['username']
    mobile = account['account']['mobile']
    balance = round(user['balance'], 2)
    tarif = tarif_info['tarif']['descr']
    shape = tarif_info['tarif']['shape']
    rent = tarif_info['tarif']['rent']

    sessions = client.service.getSessionsRadius(flt={'agentid': '1'}, )

    for session in sessions[1]:
        if session['vgid'] == user['vgid']:
            x = bin(session['assignedip'])[2:].zfill(32)
            x1 = int(x[0:8], base=2)
            x2 = int(x[8:16], base=2)
            x3 = int(x[16:24], base=2)
            x4 = int(x[24:], base=2)
            ip = f'{x1}.{x2}.{x3}.{x4}'
            ip_address = ip
            session_status = 'Сессия активна'
            mac = session['sessani']
            start_time = session['starttime']

    if 'address' in user:
        address_list = user['address'][0]['address'].split(',')
        address = address_list[3] + ' ' + address_list[5] + ' ' + address_list[6] + ' '
        city = address[3]
        street = address[5]
        house = address[6]
        if len(address_list[7]) > 0:
            address = address + address_list[7]
    else:
        address = "~"

    if block_id == 0:
        block = 'Активная'
    elif block_id == 4:
        block = 'Заблокирована по балансу'
    elif block_id == 10:
        block = 'Учетная запись отключена'
    else:
        block = 'Заблокирована, причина: ' + str(block_id)

    if session_status == 'Сессия активна':
        info_for_user = f'''
Абонент: {abonent_name};
Телефон: {mobile};
Адрес: {address};
Баланс: {balance} тг;
Статус у.з.: {block};
Сессия: {session_status};
Время начала: {start_time};
Ip: {ip_address}.
    '''
    else:
        info_for_user = f'''
Абонент: {abonent_name};
Телефон: {mobile};
Адрес: {address};
Баланс: {balance} тг;
Статус у.з.: {block};
Сессия: {session_status}.
            '''

    return info_for_user
