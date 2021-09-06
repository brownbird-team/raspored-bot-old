#   ____                                    _   ____        _   
#  |  _ \ __ _ ___ _ __   ___  _ __ ___  __| | | __ )  ___ | |_ 
#  | |_) / _` / __| '_ \ / _ \| '__/ _ \/ _` | |  _ \ / _ \| __|
#  |  _ < (_| \__ \ |_) | (_) | | |  __/ (_| | | |_) | (_) | |_ 
#  |_| \_\__,_|___/ .__/ \___/|_|  \___|\__,_| |____/ \___/ \__|
#                 |_|                         

# Made by BrownBird team
# Discord bot used to look for daily schedule changes on tsrb.hr

# Bot version
version = '2.1.5'

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
import json

# Print version in console (in color)
def prRed(skk): print("\033[91m{}\033[00m" .format(skk))
prRed("RasporedBot\n")
prRed("Version: " + version)
prRed("Made by BrownBird Team\n")

# Create function to print stuff to console
def rasprint(message): print( '[\033[91mRasporedBot\033[00m] [' + strftime('%H:%M:%S', localtime()) + '] ' + message)

# Create file config.yml if doesn't exist
if(os.path.isfile('config.yml') == False):
    rasprint('config.yml not found')
    rasprint('Creating config.yml ...')
    config = """\
# This is a settings file for Raspored bot
# Don't delete settings in this file

settings:
  # Enter your bots token here
  token: ''
  # Bot prefix (prefix for bot commands)
  bot_prefix: '.'
"""
    with open('config.yml', 'x') as f:
        f.write(config)
    rasprint('Please configure bot in config.yml and restart it')
    exit()

# Create file database.json if doesn't exist to store server data
if os.path.isfile('database.json') == False:
    rasprint('File database.json not found')
    rasprint('Creating file database.json...')
    data = {}
    with open('database.json', 'x') as f:
        f = f.write(json.dumps(data))

# Open file database.json and load data from it
with open('database.json', 'r') as f:
    f_data = f.read()
    data = json.loads(f_data)

# Open file config.yml and load configuration from it
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Check if settings in config.yml are configured corretly
if(config['settings']['token'] == ''):
    rasprint('There is no token in config file')
    exit()
# Print to console if test has passed
rasprint('Config OK')

# Create function to check if character in string is number
# Later used to check if class name is vaild
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# Set class names for each shift
A_classes = {'A', 'B', 'C', 'D', 'O'}
B_classes = {'E', 'F', 'G', 'M', 'N'}
# Set start variable for each shift
start_A = 1
start_B = 1
# Create dictionary to store data collected from webpage for each shift
# while bot is running
mega_dict_old_A = {}
mega_dict_old_B = {}
# Set first run variables to 0
# to tell site_check() functions to act diffrently on first run
first_run_A = 0
first_run_B = 0
# Set notify variables to 0
# When set to 1 by site_check() functions, bot will send current data from
# dictionary to discord
notify_A = 0
notify_B = 0
# Set embed color for bot
embed_color = 0xFF5733
# Debbug mode variable
debug_mode = 0

# Look for changes on site B
def site_check_B():
    # Debug mode
    if(debug_mode == 1):
        rasprint('Run B starting')
    # Add global variables and create local ones
    global start_B
    global mega_dict_old_B
    global first_run_B
    global notify_B
    global config
    mega_dict = {}
    # Set timer to value how much time bot should wait between checks
    timer = 15

    sleep(timer)

    # Make reguest and get data from the site
    try:
        source = requests.get('https://www.tsrb.hr/b-smjena/').text
    except:
        rasprint("Error occurred while getting data from site B, skipping...")
        start_B = 1
        return

    # Convert data to html code
    soup = BeautifulSoup(source, 'lxml')
    # Find iframes in the code
    tables = soup.find_all('iframe')
    # If there is no iframe print error and skip
    if(tables == None):
        rasprint("Can't get table link from site B, skipping...")
        start_B = 1
        return
    # find right iframe link in list
    for table in tables:
        tlink = table.attrs
        if 'docs.google.com' in tlink['src']:
            tablelink = tlink['src']

    # Get table code from iframe attribute
    try:
        newsource = requests.get(tablelink).text
    except:
        rasprint("Error occurred while getting data from iframe link B, skipping...")
        start_B = 1
        return
    # Convert data to html
    soup = BeautifulSoup(newsource, 'lxml')

    # Set class names for each shift
    A_classes = {'A', 'B', 'C', 'D', 'O'}
    B_classes = {'E', 'F', 'G', 'M', 'N'}

    mega_dict = {}
    mega_dict['titles'] = {}
    control = 0

    # Look for table titles in code and add them to dictinary
    for span in soup.find_all('span'):
        if(str(span.string).startswith('IZMJENE')):
            mega_dict['titles'][str(control)] = '**' + span.text + '**'
            control = control + 1

    mega_dict['tables'] = {}
    control = -1
    table_count = 0

    # Get data for each class from each table
    for table in soup.find_all('table'):
        mega_dict['tables'][str(table_count)] = {}
        # Store table shift (Prije podne / Poslije podne) in dictonary
        if(table.find('span').text.upper().startswith('POSLIJE')):
            mega_dict['tables'][str(table_count)]['shift'] = '**POSLIJE PODNE**'
        elif(table.find('span').text.upper().startswith('PRIJE')):
            mega_dict['tables'][str(table_count)]['shift'] = '**PRIJE PODNE**'

        for row in table.find_all('tr'):
            # Find cells in every row
            for cell in row.find_all('td'):
                test = 0
                # Find text in each cell
                # Check if data is right and store it to the dict if it is
                for span in cell.find_all('span'):
                    if(
                        (len(span.text) == 3) and
                        is_int(span.text[0]) and
                        (int(span.text[0]) <= 4) and
                        (int(span.text[0]) >= 1) and
                        (span.text[2] in A_classes or span.text[2] in B_classes) and
                        (span.text[1] == '.')
                    ):
                        control = 0
                        class_name = span.text
                        mega_dict['tables'][str(table_count)][class_name] = {}
                    elif(control < 10 and control > -1):
                        if(test == 0):
                            mega_dict['tables'][str(table_count)][class_name][str(control)] = ''
                            test = 1
                        mega_dict['tables'][str(table_count)][class_name][str(control)] = mega_dict['tables'][str(table_count)][class_name][str(control)] + ' ' + span.text

                    if(control == 9):
                        control = -1
                if(control != -1):
                    control = control + 1
                # If one cell goes over two colloms set next hour to same value
                if(cell.attrs['colspan'] == '2'):
                    mega_dict['tables'][str(table_count)][class_name][str(control)] = ' ' + span.text
                    control = control + 1
        # If data in table is vaild move the counter
        if(bool(mega_dict['tables'][str(table_count)])):
            table_count = table_count + 1

    # Convert data from dictionary to strings
    mega_dict_temp = {}
    for table_num, table in mega_dict['tables'].items():
        # Check if table is empty
        if(bool(table)):
            # If shift is Prije podne
            if(table['shift'] == '**PRIJE PODNE**'):
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + hour + '. sat =' + value + '\n'
                    mega_dict_temp[class_name] = mega_dict_temp[class_name] + '```\n'
            # If shift is Poslje podne
            else:
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + str(int(hour) - 2) + '. sat =' + value + '\n'
                    # End discord code block
                    mega_dict_temp[class_name] = mega_dict_temp[class_name] + '```\n'

    # Set mega_dict to converted values
    mega_dict = dict(mega_dict_temp)

    # Set Old_dict to mega_dict if this is the first run
    if(first_run_B == 0):
        mega_dict_old_B = dict(mega_dict)
        first_run_B = 1
        rasprint('Finished first run B successfully')
    # If this is not first run compare old and new dict
    # If they are diffrent set old dict to new one and notify variable to 1
    elif(mega_dict != mega_dict_old_B):
        rasprint('Changes has been made in B shift')
        mega_dict_old_B = dict(mega_dict)
        notify_B = 1

    # Sleep for 2 sec and set start variable to 1 so watch thread will restart site check
    sleep(2)
    start_B = 1
    # Debug mode
    if(debug_mode == 1):
        rasprint('Run B finished')

# Look for changes on site A
def site_check_A():
    # Debug mode
    if(debug_mode == 1):
        rasprint('Run A starting')
    # Add global variables and create local ones
    global start_A
    global mega_dict_old_A
    global first_run_A
    global notify_A
    global config
    mega_dict = {}
    # Set timer to value how much time bot should wait between checks
    timer = 15

    sleep(timer)

    # Make reguest and get data from the site
    try:
        source = requests.get('https://tsrb.hr/a-smjena/').text
    except:
        rasprint("Error occurred while getting data from site A, skipping...")
        start_A = 1
        return

    # Convert data to html code
    soup = BeautifulSoup(source, 'lxml')
    # Find iframes in the code
    tables = soup.find_all('iframe')
    # If there is no iframe print error and skip
    if(tables == None):
        rasprint("Can't get table link from site A, skipping...")
        start_A = 1
        return
    # find right iframe link in list
    for table in tables:
        tlink = table.attrs
        if 'docs.google.com' in tlink['src']:
            tablelink = tlink['src']

    # Get table code from iframe attribute
    try:
        newsource = requests.get(tablelink).text
    except:
        rasprint("Error occurred while getting data from iframe link A, skipping...")
        start_A = 1
        return
    # Convert data to html
    soup = BeautifulSoup(newsource, 'lxml')

    # Set class names for each shift
    A_classes = {'A', 'B', 'C', 'D', 'O'}
    B_classes = {'E', 'F', 'G', 'M', 'N'}

    mega_dict = {}
    mega_dict['titles'] = {}
    control = 0

    # Look for table titles in code and add them to dictinary
    for span in soup.find_all('span'):
        if(str(span.string).startswith('IZMJENE')):
            mega_dict['titles'][str(control)] = '**' + span.text + '**'
            control = control + 1

    mega_dict['tables'] = {}
    control = -1
    table_count = 0

    # Get data for each class from each table
    for table in soup.find_all('table'):
        mega_dict['tables'][str(table_count)] = {}
        # Store table shift (Prije podne / Poslije podne) in dictonary
        if(table.find('span').text.upper().startswith('POSLIJE')):
            mega_dict['tables'][str(table_count)]['shift'] = '**POSLIJE PODNE**'
        elif(table.find('span').text.upper().startswith('PRIJE')):
            mega_dict['tables'][str(table_count)]['shift'] = '**PRIJE PODNE**'

        for row in table.find_all('tr'):
            # Find cells in every row
            for cell in row.find_all('td'):
                test = 0
                # Find text in each cell
                # Check if data is right and store it to the dict if it is
                for span in cell.find_all('span'):
                    if(
                        (len(span.text) == 3) and
                        is_int(span.text[0]) and
                        (int(span.text[0]) <= 4) and
                        (int(span.text[0]) >= 1) and
                        (span.text[2] in A_classes or span.text[2] in B_classes) and
                        (span.text[1] == '.')
                    ):
                        control = 0
                        class_name = span.text
                        mega_dict['tables'][str(table_count)][class_name] = {}
                    elif(control < 10 and control > -1):
                        if(test == 0):
                            mega_dict['tables'][str(table_count)][class_name][str(control)] = ''
                            test = 1
                        mega_dict['tables'][str(table_count)][class_name][str(control)] = mega_dict['tables'][str(table_count)][class_name][str(control)] + ' ' + span.text

                    if(control == 9):
                        control = -1
                if(control != -1):
                    control = control + 1
                # If one cell goes over two colloms set next hour to same value
                if(cell.attrs['colspan'] == '2'):
                    mega_dict['tables'][str(table_count)][class_name][str(control)] = ' ' + span.text
                    control = control + 1
        # If data in table is vaild move the counter
        if(bool(mega_dict['tables'][str(table_count)])):
            table_count = table_count + 1

    # Convert data from dictionary to strings
    mega_dict_temp = {}
    for table_num, table in mega_dict['tables'].items():
        # Check if table is empty
        if(bool(table)):
            # If shift is Prije podne
            if(table['shift'] == '**PRIJE PODNE**'):
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + hour + '. sat =' + value + '\n'
                    mega_dict_temp[class_name] = mega_dict_temp[class_name] + '```\n'
            # If shift is Poslje podne
            else:
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + mega_dict['titles'][table_num] + '\n' + table['shift'] + '\n```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        mega_dict_temp[class_name] = mega_dict_temp[class_name] + str(int(hour) - 2) + '. sat =' + value + '\n'
                    # End discord code block
                    mega_dict_temp[class_name] = mega_dict_temp[class_name] + '```\n'

    # Set mega_dict to converted values
    mega_dict = dict(mega_dict_temp)

    # Set Old_dict to mega_dict if this is the first run
    if(first_run_A == 0):
        mega_dict_old_A = dict(mega_dict)
        first_run_A = 1
        rasprint('Finished first run A successfully')
    # If this is not first run compare old and new dict
    # If they are diffrent set old dict to new one and notify variable to 1
    elif(mega_dict != mega_dict_old_A):
        rasprint('Changes has been made in A shift')
        mega_dict_old_A = dict(mega_dict)
        notify_A = 1

    # Sleep for 2 sec and set start variable to 1 so watch thread will restart site check
    sleep(2)
    start_A = 1
    # Debug mode
    if(debug_mode == 1):
        rasprint('Run A finished')

# Start site check again when its done
def watch():
    global start_A
    global start_B
    while True:
        sleep(1)
        # If site_check for A shift is done start it again
        if start_A == 1:
            start_A = 0
            site_check_A_thread = threading.Thread(target = site_check_A)
            site_check_A_thread.start()
        # If site_check for B shift is done start it again
        if start_B == 1:
            start_B = 0
            site_check_B_thread = threading.Thread(target = site_check_B)
            site_check_B_thread.start()

# Get input from console
def get_input():
    global debug_mode
    global notify_A
    global notify_B
    while True:
        value = input()
        if(value == 'list'):
            rasprint('List of servers in database:')
            for k, v in data.items():
                rasprint('- ' + data[k]['name'])
        if(value == 'debug on'):
            debug_mode = 1
            rasprint('Debug mode on')
        if(value == 'debug off'):
            debug_mode = 0
            rasprint('Debug mode off')
        if(value == 'notify a'):
            rasprint('Sending last change to all configured servers in A shift')
            notify_A = 1
        if(value == 'notify b'):
            rasprint('Sending last change to all cinfigured servers in B shift')
            notify_B = 1

# Start get input from console thread
get_input_thread = threading.Thread(target=get_input)
get_input_thread.start()

# Start watch thread
watch_thread = threading.Thread(target=watch)
watch_thread.start()



# Ativate discord logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = 'discord.log', encoding = 'utf-8', mode = 'w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Create client variable
client = commands.Bot(command_prefix = config['settings']['bot_prefix'], help_command = None)

@client.event
# When bot is ready
async def on_ready():
    # Start loop to check notify variable
    my_loop.start()
    # Print info to console
    rasprint('Connected to bot: {}'.format(client.user))
    rasprint('Bot ID: {}'.format(client.user.id))
    rasprint('Ready to ROCK')
    # Set bot status
    await client.change_presence(
        activity=discord.Activity(type = discord.ActivityType.watching, name = 'for .help'))
    # Check if all servers are in database.json
    # If they are not add them and write to the file
    for server in client.guilds:
        if str(server.id) not in data:
            data[str(server.id)] = {}
            data[str(server.id)]['name'] = str(server.name)
            data[str(server.id)]['channel_id'] = None
            data[str(server.id)]['channel_name'] = None
            data[str(server.id)]['class'] = None
            data[str(server.id)]['shift'] = None
            with open('database.json', 'w') as f:
                f.write(json.dumps(data))

@client.event
# When bot joins the server add the server to database.json file
async def on_guild_join(guild):
    server_id = discord.utils.get(client.guilds, name=str(guild.name)).id
    data[str(server_id)] = {}
    data[str(server_id)]['name'] = str(guild.name)
    data[str(server_id)]['channel_id'] = None
    data[str(server_id)]['channel_name'] = None
    data[str(server_id)]['class'] = None
    data[str(server_id)]['shift'] = None
    with open('database.json', 'w') as f:
        f.write(json.dumps(data))

# Create my_loop to look for if changes are made and send them to discord
@tasks.loop(seconds=1)
async def my_loop():
    global notify_A
    global notify_B
    # Check if changes are made in A shift
    if(notify_A == 1):
        # Send changes to all A shift servers in database
        for server in client.guilds:
            # Skip server if not configured or not in A shift
            if data[str(server.id)]['channel_id'] != None and data[str(server.id)]['class'] != None and data[str(server.id)]['class'][2] in A_classes:
                channel = client.get_channel(data[str(server.id)]['channel_id'])
                description = mega_dict_old_A[data[str(server.id)]['class']]
                embed=discord.Embed(
                    title='Raspored ' + data[str(server.id)]['class'],
                    url='https://www.tsrb.hr/a-smjena/',
                    description = description,
                    color = embed_color)
                await channel.send(embed=embed)
        # Set notify variable back to 0
        notify_A = 0
    # Check if changes are made in B shift
    if(notify_B == 1):
        # Send changes to all B shift servers in database
        for server in client.guilds:
            # Skip server if not configured or not in B shift
            if data[str(server.id)]['channel_id'] != None and data[str(server.id)]['class'] != None and data[str(server.id)]['class'][2] in B_classes:
                channel = client.get_channel(data[str(server.id)]['channel_id'])
                description = mega_dict_old_B[data[str(server.id)]['class']]
                embed=discord.Embed(
                    title='Raspored ' + data[str(server.id)]['class'],
                    url='https://www.tsrb.hr/b-smjena/',
                    description = description,
                    color = embed_color)
                await channel.send(embed=embed)
        # Set notify variable back to 0
        notify_B = 0

# Add conf command group
@client.group(pass_context = True)
# Command can be used only in servers
@commands.guild_only()
# Command can be used only by admins
@commands.has_permissions(administrator = True)
async def conf(ctx):
    # Display message with no attribute
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(title='Konfiguriranje Bota', color = embed_color)
        embed.add_field(name = '.conf kanal', value = 'Napišite ovu komandu u kanal gdje želite dobivati obavjesti.', inline = False)
        embed.add_field(name = '.conf raz <ime razreda>', value = 'Definirajte željeni razred, zamjenite `<ime razreda>` sa svojim razredom.', inline = False)
        embed.add_field(name = '.conf obrisi', value = 'Poništite konfiguraciju bota.', inline = False)
        await ctx.send(embed = embed)

# Add conf subcommand kanal, set channel in database to channel where command is issued
@conf.command()
async def kanal(ctx):
    channel_id = discord.utils.get(ctx.guild.channels, name=str(ctx.channel)).id
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    data[str(server_id)]['channel_id'] = channel_id
    data[str(server_id)]['channel_name'] = str(ctx.channel)
    with open('database.json', 'w') as f:
        f.write(json.dumps(data))
    embed = discord.Embed(
        title = 'Kanal za obavjesti',
        description = 'Kanal za obavjesti je postavljen na **{}**,\n Ovdje ćete primiti obavjest kada se raspored promjeni.'.format(str(ctx.channel)),
        color = embed_color
    )
    await ctx.send(embed = embed)

# Add conf subcommand raz, set class in database to class defined as attribute of the command
@conf.command()
async def raz(ctx, class_name: str):

    class_name = class_name.upper()

    # Check if defined class is vaild
    if(
        (len(class_name) != 3) or
        not is_int(class_name[0]) or
        (int(class_name[0]) > 4) or
        (int(class_name[0]) < 1) or
        (class_name[2] not in A_classes and class_name[2] not in B_classes) or 
        (class_name[1] != '.')
    ):  
        # If class is not vaild, send error message
        await ctx.send("Napišite razred pravilno (primjer: 2.G)")
        return
    
    # If class is vaild save it in database
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    data[str(server_id)]['class'] = class_name
    # Determine in which shift class is
    if(class_name[2] in A_classes):
        data[str(server_id)]['shift'] = 'A'
    else:
        data[str(server_id)]['shift'] = 'B'
    
    # Write changes to database.json
    with open('database.json', 'w') as f:
        f.write(json.dumps(data))
    
    # Create discord embed and send it to comfirm succesful data saving
    embed = discord.Embed(
        title = 'Razred',
        description = 'Razred je postavljen na **{}** u **{}** smjeni, bit ćete informirani kada dođe do promjena u rasporedu za taj razred.'.format(class_name, data[str(server_id)]['shift']),
        color = embed_color
    )
    await ctx.send(embed = embed)

# Add conf subcommand status, Display information from database for your server
@conf.command()
async def status(ctx):
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    embed = discord.Embed(
        title = 'Status Konfiguracija',
        color = embed_color
    )
    embed.add_field(name = 'Razred', value = '```' + str(data[str(server_id)]['class']) + '```', inline = True)
    embed.add_field(name = 'Smjena', value = '```' + str(data[str(server_id)]['shift']) + '```', inline = True)
    embed.add_field(name = 'Kanal za obavjesti', value = '```' + str(data[str(server_id)]['channel_name']) + '```', inline = False)
    await ctx.send(embed = embed)

# Add conf subcommand obrisi, clear all configurations for the server
@conf.command()
async def obrisi(ctx):
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    data[str(server_id)]['class'] = None
    data[str(server_id)]['shift'] = None
    data[str(server_id)]['channel_id'] = None
    data[str(server_id)]['channel_name'] = None
    with open('database.json', 'w') as f:
        f.write(json.dumps(data))
    await ctx.send('Sve konfiguracije su obrisane iz baze podataka')

# Add command raspored to send last changes, for class defined in database, or specified as command attribute
@client.command()
async def raspored(ctx, name = None):
    # Send error if first run is not done yet
    if(first_run_A == 0 or first_run_B == 0):
        embed = discord.Embed(title = 'ZAHTJEV ODBIJEN', description = 'Pričekaj, povlačim podatke sa stranice\n ovo može potrajati do 30 s', color = embed_color)
    # If commands has no argument and is send in server
    elif(name == None and ctx.guild != None):
        server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
        # If class is configured in that server
        if(data[str(server_id)]['class'] != None):
            class_name = data[str(server_id)]['class']
            # If configured class is in A shift
            if data[str(server_id)]['class'][2] in A_classes:
                description = mega_dict_old_A[data[str(server_id)]['class']]
                url = 'https://www.tsrb.hr/a-smjena/'
            # If configured class is in B shift
            else:
                description = mega_dict_old_B[data[str(server_id)]['class']]
                url = 'https://www.tsrb.hr/b-smjena/'
            embed = discord.Embed(title = "Raspored " + class_name, url = url, description = description, color = embed_color)
        # If class is not configured set embed to an error
        else:
            embed = discord.Embed(title = "Razred nije definiran", description = "Kako bi ste koristili ovu komandu potrebno je definirati razred", color = embed_color)
            embed.add_field(name = 'Definirajte razred (Admin)', value = '```.conf raz <ime razreda>```', inline = False)
            embed.add_field(name = 'Napišite željeni razred u komandi', value = '```.raspored <ime razreda>```', inline = False)
    # If there is no argument and command was send in PM, set embed to an error
    elif(name == None and ctx.guild == None):
        embed = discord.Embed(title = "Razred nije definiran", description = "Kako bi ste koristili bota u privatnim porukama potrebno je definirati razred.", color = embed_color)
        embed.add_field(name = 'Primjer', value = '```.raspored <ime razreda>```', inline = False)
    # If there class as argument
    elif(name != None):
        # Set argument to upper case
        name = name.upper()
        # Check if specified class name exist
        if(
            (len(name) != 3) or
            not is_int(name[0]) or
            (int(name[0]) > 4) or
            (int(name[0]) < 1) or
            (name[2] not in A_classes and name[2] not in B_classes) or 
            (name[1] != '.')
        ):
            embed = discord.Embed(title = "Razred nije pravilno definiran", description = "Traženi razred nije pronađen.", color = embed_color)
            embed.add_field(name = 'Primjer', value = '```.raspored <ime razreda>```', inline = False)
        else:
            if name[2] in A_classes:
                description = mega_dict_old_A[name]
                url = 'https://www.tsrb.hr/a-smjena/'
            else:
                description = mega_dict_old_B[name]
                url = 'https://www.tsrb.hr/b-smjena/'
            embed = discord.Embed(title = "Raspored " + name, url = url, description = description, color = embed_color)
    await ctx.send(embed=embed)

# Add help command to display help message
@client.command()
async def help(ctx):
    description = """\
Ovo je lista komadi raspored bota i upute za korištenje,
samo administratori servera mogu izvršiti komande označene sa (Admin).
Komande koje se mogu koristiti i u privatnim porukama su označene sa (Private).
**Napomena:** bot će automatski slati obavjesti samo ako su i kanal i razred konfigurirani"""
    embed = discord.Embed(
        title = 'Pomoć (Help)',
        description = description,
        color = embed_color
    )
    embed.add_field(
        name = 'Raspored',
        value = '```.raspored```\nOva komanda ispisat će posljednje izmjene u rasporedu za razred definiran pri konfiguraciji, te se neće izvršiti ukoliko razred nije definiran.',
        inline = False
    )
    embed.add_field(
        name = 'Raspored za razred (Private)',
        value = '```.raspored <ime razreda>```\nOva komanda ispisat će posljednje izmjene za razred naveden u komandi.\n(Također radi i u PM)',
        inline = False
    )
    embed.add_field(
        name = 'Verzija Bota (Private)',
        value = '```.ver```\nIspisuje Verziju bota',
        inline = False
    )
    embed.add_field(
        name = 'Pomoć (Private)',
        value = '```.help```\nIspisuje ovu poruku',
        inline = False
    )
    embed.add_field(
        name = 'Konfiguracija kanala (Admin)', 
        value = '```.conf kanal```\nU kanal u kojem je izvršena komanda bot će slati obavjesti kada se raspored promjeni.',
        inline = False
        )
    embed.add_field(
        name = 'Konfiguracija razreda (Admin)',
        value = '```.conf raz <ime razreda>```\nZa razred koji je naveden u komandi bot će slati obavjesti kada se raspored promjeni.',
        inline = False
        )
    embed.add_field(
        name = 'Brisanje konfiguracije (Admin)',
        value = '```.conf obrisi```\nUkoliko želite poništiti konfiguraciju bota za vaš server, izvršite ovu komandu.'
    )
    await ctx.send(embed = embed)

# Add version command to display bot version
@client.command()
async def ver(ctx):
    await ctx.send(
        'Koristite **Raspored Bot** verzija **' + version + '**\nMade by BrownBird Team'
    )

@raz.error
async def raz_error(ctx, error):
    # Send error message when class in not specified after raz command
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("Razred nije definiran u komandi. Napišite .help za pomoć.")

@conf.error
async def conf_error(ctx, error):
    # Send error message if non admin try to execute command
    if isinstance(error, discord.ext.commands.errors.MissingPermissions):
        await ctx.send("Nemate ovlasti za izvršavanje ove komande.")
    # Send error message if executed as private message
    if isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send("Ova komanda se ne može koristiti u privatnim porukama.")

    
# Run client with token form config.yml
while True:
    try:
        client.run(config['settings']['token'])
    except:
        rasprint('Error while connecting to discord')
        sleep(1)