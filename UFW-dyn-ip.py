#!/usr/bin/env python3
# Copyright 2022 Innovara Ltd
# -*- coding: utf-8 -*-
# Licensed under the GNU General Public License, version 3. This file may not be
# copied, modified, or distributed except according to those terms.

import json
import os
import subprocess

from dns.resolver import Resolver
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
        s = {}
        s['app'] = ''
        s['last_check'] = ''
        s['last_ip'] = ''
        s['last_update'] = ''
        s['ports'] = []
        s['to'] = ''
        with open(settings, 'w', encoding='utf-8') as config:
            json.dump(s, config, sort_keys=True, indent=4)
            os.chmod(settings, 0o600)
        print("Edit {} and try again.".format(settings))
        return
    # Get current ip
    public_ip = get('https://api.ipify.org').text
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Update src IP if different from previous
    if public_ip != config['last_ip'] and config['last_ip']:
        # Delete previous allow rules
        run("/usr/sbin/ufw delete allow from {} to {} app {}".format(config['last_ip'], config['to'], config['app']))
        # Add new allow rules
        run("/usr/sbin/ufw allow from {} to {} app {}".format(public_ip, config['to'], config['app']))
        config['last_ip'] = public_ip
        config['last_check'] = time
        config['last_update'] = time
    else:
        config['last_ip'] = public_ip
        config['last_check'] = time
    # Update settings
    with open(settings, "w") as file:
        new_settings = json.dumps(config, sort_keys=True, indent=4)
        file.write(new_settings)


if __name__ == '__main__':
    main()
