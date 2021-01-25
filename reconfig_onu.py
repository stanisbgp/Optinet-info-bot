#!/usr/bin/python3.6

import telnetlib
import config
from pyzabbix import ZabbixAPI
from suds.client import Client


USERNAME = config.telnet_login
PASSWORD = config.telnet_password


def reconfig_epon_port(message):

    global ip_device, port_onu, login_id, vlan

    port_epon = ''
    sequence = ''
    endpoint = config.wsdl_url
    service_url = config.service_url
    client = Client(endpoint, faults=False)
    client.set_options(location=service_url)
    manager = client.service.Login(config.billing_login, config.billing_password)

    login_id = message.text
    users = client.service.getVgroups(flt={'login': login_id})
    port = client.service.getPorts(flt={'vgid': users[1][0]['vgid']})
    device = client.service.getDevice(id=port[1][0]['deviceid'])
    devicename = device[1][0]['device']['devicename']
    ip_device = device[1][0]['options'][0]['value']


# Epon port setting
    zb = ZabbixAPI('http://zabbix.opti', user=config.zabbix_login, password=config.zabbix_password)
    items = zb.item.get(host=devicename, output=['itemid', 'name', 'lastvalue'])
    for item in items:
        if str(login_id) in item['name']:
            if 'status' in item['name']:
                item_name = item['name'].split()
                item_name = item_name[1].split('(')
                port_onu = item_name[0]
                port_value = port_onu.split(':')
                sequence = port_value[1]
                port_epon = port_value[0]
                vlan = (int(port_epon.split('/')[1]) * 100) + int(port_value[1])

    HOST = ip_device
    tn = telnetlib.Telnet(HOST)

    tn.read_until(b"Username: ")
    tn.write(USERNAME.encode('ascii') + b"\n")
    if PASSWORD:
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")
    tn.write(b'config\n')
    config_epon_port = f'interface {port_epon}\n'
    config_epon_port = config_epon_port.encode('ASCII')
    tn.write(config_epon_port)
    delete_onu = f'no epon bind-onu sequence {sequence}\n'
    delete_onu = delete_onu.encode('ASCII')
    tn.write(delete_onu)
    tn.write(b'exit\n')
    tn.write(b'exit\n')
    tn.write(b'exit\n')
    tn.write(b'exit\n')
    tn.read_all().decode('ascii')


# Onu port settnig
def reconfig_onu_port():

    global ip_device, port_onu, login_id, vlan

    HOST = ip_device
    tn = telnetlib.Telnet(HOST)

    tn.read_until(b"Username: ")
    tn.write(USERNAME.encode('ascii') + b"\n")
    if PASSWORD:
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")

    tn.write(b'config\n')
    config_onu_port = f'interface {port_onu}\n'
    config_onu_port = config_onu_port.encode('ASCII')
    tn.write(config_onu_port)
    description_port = f'description {login_id}\n'
    description_port = description_port.encode('ASCII')
    tn.write(description_port)
    config_vlan_on_port = f'epon onu port 1 ctc vlan mode tag {vlan}\n'
    config_vlan_on_port = config_vlan_on_port.encode('ASCII')
    tn.write(config_vlan_on_port)
    absent_config_mode = f"This ONU({port_onu}) is not auto-configured. Are you sure to use absent-config-mode(y/n)?"
    absent_config_mode = absent_config_mode.encode('ASCII')
    response = tn.read_until(absent_config_mode, timeout=10)
    if b'Are you sure to use absent-config-mode(y/n)?' in response:
        tn.write(b'y\n')
    tn.write(b'exit\n')
    tn.write(b'exit\n')
    tn.write(b'write all\n')
    tn.write(b'exit\n')
    tn.write(b'exit\n')
    tn.read_all().decode('ascii')
    answer_end_config = 'Настройка завершена'
    return answer_end_config

