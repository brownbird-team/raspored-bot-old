#   ____                                    _   ____        _   
#  |  _ \ __ _ ___ _ __   ___  _ __ ___  __| | | __ )  ___ | |_ 
#  | |_) / _` / __| '_ \ / _ \| '__/ _ \/ _` | |  _ \ / _ \| __|
#  |  _ < (_| \__ \ |_) | (_) | | |  __/ (_| | | |_) | (_) | |_ 
#  |_| \_\__,_|___/ .__/ \___/|_|  \___|\__,_| |____/ \___/ \__|
#                 |_|                         

# Made by BrownBird team
# Discord bot used to look for daily schedule changes on tsrb.hr/b-smjena

# Bot version
ver = '2.0.0'

# Import stuff
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext import tasks
from  time import *
import requests
import threading
import discord
import logging
import os
import yaml

def prRed(skk): print("\033[91m{}\033[00m" .format(skk))

prRed('88""Yb    db    .dP"Y8 88""Yb  dP"Yb  88""Yb 888888 8888b.     88""Yb  dP"Yb  888888 ')
prRed('88__dP   dPYb   `Ybo." 88__dP dP   Yb 88__dP 88__    8I  Yb    88__dP dP   Yb   88   ')
prRed('88"Yb   dP__Yb  o.`Y8b 88"""  Yb   dP 88"Yb  88""    8I  dY    88""Yb Yb   dP   88   ')
prRed('88  Yb dP""""Yb 8bodP" 88      YbodP  88  Yb 888888 8888Y"     88oodP  YbodP    88   ')
prRed('')
prRed("Version: " + str(ver))
prRed("Made by BrownBird Team\n")

# Create file config.yml if doesn't exist
if(os.path.isfile('config.yml') == False):
    print('config.yml not found')
    print('Creating config.yml ...')
    config = """\
# This is a settings file for Raspored bot
# Don't delete settings in this file

settings:
  # Enter your school class here (example: 2.G)
  class: ''
  # Enter your bots token here
  token: ''
  # Channel ID of channel in which bot should post when schedule changes
  channel_id:
  # Bot prefix (prefix for bot commands)
  bot_prefix: '.'
  # If set to true bot will work in holidays mode
  # This setting can be changed while bot is working
  holidays: false
"""
    with open('config.yml', 'x') as f:
        f.write(config)
    print('Please configure bot in config.yml and restart it')
    exit()

# Open config file
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Check if bot is configured corretly
if(config['settings']['class'] == ''):
    print('There is no class in config file')
    exit()
if(config['settings']['token'] == ''):
    print('There is no token in config file')
    exit()
if(config['settings']['channel_id'] == None):
    print('There is no channel ID in config file')
    exit()
print('Config OK\nSchool class set to: ' + config['settings']['class'])

# Set global variables
start = 1
mega_string_old = ''
mega_string = ''
first_run = 0
notify = 0

# Look for changes on site
def site_check():
    global start
    global mega_string
    global mega_string_old
    global first_run
    global notify
    global config
    timer = 15

    sleep(timer)
    class_name = config['settings']['class']
    source = requests.get('https://tsrb.hr/b-smjena/').text

    soup = BeautifulSoup(source, 'lxml')
    table = soup.find('iframe')
    tablelink = table.attrs

    newsource = requests.get(tablelink['src']).text
    soup = BeautifulSoup(newsource, 'lxml')

    control = 0

    for i in soup.find_all('span'):
        if(str(i.string).startswith('IZMJENE')):
            mega_string = mega_string + '**' + i.text + '**' + "\n" + '```'
        if(i.string == class_name):
            control = 1
        elif(control < 10 and control > 0):
            mega_string = mega_string + str(control) + '. sat = ' + i.text + '\n'
            if(control == 9):
                mega_string = mega_string + '```' + '\n'
            control = control + 1
    if(first_run == 0):
        mega_string_old = mega_string
        first_run = 1
        print('Finished first run Ready')
    elif(mega_string_old != mega_string):
                mega_string_old = mega_string
                notify = 1
    mega_string = ''
    start = 1
    sleep(2)

# Start site check again when its done
def watch():
    global start
    while True:
        sleep(1)
        if start == 1:
            start = 0
            site_check_thread = threading.Thread(target = site_check)
            site_check_thread.start()

watch_thread = threading.Thread(target=watch)
watch_thread.start()



# Ativate logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = 'discord.log', encoding = 'utf-8', mode = 'w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Create client variable
client = commands.Bot(command_prefix = config['settings']['bot_prefix'])

# Do the following when bot is ready
@client.event
async def on_ready():
    my_loop.start()
    print('Connected to bot: {}'.format(client.user))
    print('Bot ID: {}'.format(client.user.id))
    await client.change_presence(
        activity=discord.Activity(type = discord.ActivityType.watching, name = 'for something')
        )

# Create my_loop to look for if changes are made and send them to discord
@tasks.loop(seconds=1)
async def my_loop():
    global notify
    if(notify == 1):
        channel = client.get_channel(config['settings']['channel_id'])
        embed=discord.Embed(title='Raspored ' + config['settings']['class'], url='https://www.tsrb.hr/b-smjena/', description = mega_string_old, color = 0xFF5733)
        await channel.send(embed=embed)
        notify = 0

# Create a command to ask bot directly for the changes
@client.command()
async def raspored(ctx):
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
    if(first_run == 0):
        embed = discord.Embed(title = 'ZAHTJEV ODBIJEN', description = 'Pričekaj, povlačim podatke sa stranice\n ovo može potrajati do 20 s', color = 0xFF5733)
    elif(config['settings']['holidays']):
        embed = discord.Embed(title = 'PRAZNICI', description = 'Praznici su u tijeku, za sada nema rasporeda.', color = 0xFF5733)
    else:
        embed = discord.Embed(title = "Raspored " + config['settings']['class'], url = 'https://www.tsrb.hr/b-smjena/', description = mega_string_old, color = 0xFF5733)
    await ctx.send(embed=embed)

# Create a version command to display bot version
@client.command()
async def version(ctx):
    await ctx.send(
        'Koristite **Raspored Bot** verzija **' + ver + '**\nMade by BrownBird Team'
    )

    
# Run client
client.run(config['settings']['token'])
