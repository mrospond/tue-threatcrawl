"""This file saves user input from the GUI and starts a crawler process

When the user has clicked the Start Crawling button in the GUI, it will run this file. The username and password are
retrieved and given as arguments when launching the main process. The other user input will be saved to a temporary
json file, such that main.py can retrieve them. The username and password are never saved in the json file!

By launching main.py, the crawler and cli are started."""

import sys
import json
import subprocess

# Retrieve input values
data = sys.stdin.readline()
data = json.loads(data)

username = data['username']
password = data['password']
configuration_id = data['configuration_id']

# Start a terminal and run the CLI. Also pass the username, password and configuration ObjectId
subprocess.call(['gnome-terminal', '-e', f'python3 main.py {username} {password} {configuration_id}'])
