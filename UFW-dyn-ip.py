#!/usr/bin/env python3
# Copyright 2022 Innovara Ltd
# -*- coding: utf-8 -*-
# Licensed under the GNU General Public License, version 3. This file may not be
# copied, modified, or distributed except according to those terms.

import json
import os
import subprocess

from requests import get
from datetime import datetime


def run(cmd):
    process = subprocess.Popen(['bash', '-c', cmd],
                     stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8')


def main():
    settings = 'config.json'
    # Open settings file
    try:
        with open(settings, 'r') as file:
            config = json.load(file)
    # Create settings file if it doesn't exist
    except FileNotFoundError:
        print("Settings file not found. Creating.")

        template = {
            'my.example.com' : {
                'apps' : [],
                'comment' : 'added by UFW-dyn',
                'last_check' : '',
                'last_ip' : {
                    'ipv4' : '',
                    'ipv6' : ''
                },
                'last_update' : '',
                'ports' : {
                    'tcp' : [],
                    'udp' : []
                },
                'to' : {
                    'ipv4' : 'any',
                    'ipv6' : 'any'
                },
                'verbose' : False
            }
        }

        with open(settings, 'w', encoding='utf-8') as config:
            json.dump(template, config, sort_keys=True, indent=4)
            os.chmod(settings, 0o600)
        print("Edit {} and try again.".format(settings))
        return
    # If the file is currupt, suggest creating a new one
    except json.decoder.JSONDecodeError:
        print("{} could not be loaded. Rename or delete file to create a new template.".format(settings))
        return
    for domain in config:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for ipv in config[domain]['last_ip']:
            # Get current IPv4
            if ipv == 'ipv4':
                public_ip = get('https://api.ipify.org').text
            # Get current IPv6
            elif ipv == 'ipv6':
                public_ip = get('https://api64.ipify.org').text
            if config[domain]['verbose'] == True:
                print("current "+ipv+" "+public_ip)
                print("last "+ipv+" "+config[domain]['last_ip'][ipv])
                print("to "+config[domain]['to'][ipv])
            # Update src IP if different from previous
            if public_ip != config[domain]['last_ip'][ipv] \
                and config[domain]['to'][ipv]:
                # Update app-based rules
                if config[domain]['apps']:
                    for app in config[domain]['apps']:
                        # Delete previous allow rule
                        if config[domain]['last_ip'][ipv]:
                            if config[domain]['verbose'] == True:
                                print("/usr/sbin/ufw delete allow from {} to {} app {}".format(config[domain]['last_ip'][ipv], config[domain]['to'][ipv], app))
                            run("/usr/sbin/ufw delete allow from {} to {} app {}".format(config[domain]['last_ip'][ipv], config[domain]['to'][ipv], app))
                        # Add allow rule
                        if config[domain]['verbose'] == True:
                            print("/usr/sbin/ufw allow from {} to {} app {} comment '{}'".format(public_ip, config[domain]['to'][ipv], app, config[domain]['comment']))
                        run("/usr/sbin/ufw allow from {} to {} app {} comment '{}'".format(public_ip, config[domain]['to'][ipv], app, config[domain]['comment']))
                # Update port-based rules
                for proto in config[domain]['ports']:
                    for port in config[domain]['ports'][proto]:
                        # Delete previous allow rule
                        if config[domain]['last_ip'][ipv]:
                            if config[domain]['verbose'] == True:
                                print("/usr/sbin/ufw delete allow from {} to {} port {} proto {}".format(config[domain]['last_ip'][ipv], config[domain]['to'][ipv], port, proto))
                            run("/usr/sbin/ufw delete allow from {} to {} port {} proto {}".format(config[domain]['last_ip'][ipv], config[domain]['to'][ipv], port, proto))
                        # Add allow rule
                        if config[domain]['verbose'] == True:
                            print("/usr/sbin/ufw allow from {} to {} port {} proto {} comment '{}'".format(public_ip, config[domain]['to'][ipv], port, proto, config[domain]['comment']))
                        run("/usr/sbin/ufw allow from {} to {} port {} proto {} comment '{}'".format(public_ip, config[domain]['to'][ipv], port, proto, config[domain]['comment']))
                config[domain]['last_ip'][ipv] = public_ip
                config[domain]['last_check'] = time
                config[domain]['last_update'] = time
            else:
                if config[domain]['verbose'] == True:
                    print("No rules updated")
                config[domain]['last_ip'][ipv] = public_ip
                config[domain]['last_check'] = time
        # Update settings
        with open(settings, "w") as file:
            new_settings = json.dumps(config, sort_keys=True, indent=4)
            file.write(new_settings)


if __name__ == '__main__':
    main()
