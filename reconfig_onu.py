#!/usr/bin/python3.6

import telnetlib
import config
from pyzabbix import ZabbixAPI
from suds.client import Client


def reconfig_onu(login_id):
    endpoint = config.wsdl_url
    service_url = config.service_url
    client = Client(endpoint, faults=False)
    client.set_options(location=service_url)
    manager = client.service.Login(config.billing_login, config.billing_password)

    users = client.service.getVgroups(flt={'login': login_id})
    port = client.service.getPorts(flt={'vgid': users[1][0]['vgid']})
    device = client.service.getDevice(id=port[1][0]['deviceid'])
    devicename = device[1][0]['device']['devicename']
    ip_device = device[1][0]['options'][0]['value']

    HOST = ip_device
    USERNAME = config.telnet_login
    PASSWORD = config.telnet_password
    tn = telnetlib.Telnet(HOST)

    zb = ZabbixAPI('http://zabbix.opti', user=config.zabbix_login, password=config.zabbix_password)
    items = zb.item.get(host=devicename, output=['itemid', 'name', 'lastvalue'])
    for item in items:
        if str(login_id) in item['name']:
            if 'status' in item['name']:
                item_name = item['name'].split()
                item_name = item_name[1].split('(')
                port_onu = item_name[0]
                port_value = port_onu.split(':')
                port_epon = port_value[0]
                vlan = (int(port_epon.split('/')[1]) * 100) + int(port_value[1])

    tn.read_until(b"Username: ")
    tn.write(USERNAME.encode('ascii') + b"\n")
    if PASSWORD:
        tn.read_until(b"Password: ")
        tn.write(PASSWORD.encode('ascii') + b"\n")

    tn.write(b'config\n')
    config_port = f'interface {port_onu}\n'
    config_port = config_port.encode('ASCII')
    tn.write(config_port)
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
    answer_end_config = 'Настройка завершена'
    return answer_end_config
