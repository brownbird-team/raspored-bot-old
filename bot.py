#   ____                                    _   ____        _   
#  |  _ \ __ _ ___ _ __   ___  _ __ ___  __| | | __ )  ___ | |_ 
#  | |_) / _` / __| '_ \ / _ \| '__/ _ \/ _` | |  _ \ / _ \| __|
#  |  _ < (_| \__ \ |_) | (_) | | |  __/ (_| | | |_) | (_) | |_ 
#  |_| \_\__,_|___/ .__/ \___/|_|  \___|\__,_| |____/ \___/ \__|
#                 |_|                         

# Made by BrownBird team
# Discord bot used to look for daily schedule changes on tsrb.hr

# Bot version
version = '2.4.0'

# Import stuff
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from aioconsole import ainput
from datetime import date
from  time import *
import asyncio
import requests
import discord
import logging
import os
import re
import yaml
import json

# Print version in console (in color)
def prRed(skk): print("\u001b[32m{}\033[00m" .format(skk))
prRed("RasporedBot\n")
prRed("Version: " + version)
prRed("Made by BrownBird Team\n")

# Create function to print stuff to console
def rasprint(message):
    print( '[\u001b[32mRasporedBot\033[00m] [' + date.today().strftime('%d-%m-%Y') + '] [' + strftime('%H:%M:%S', localtime()) + '] ' + message)

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
  # Time to wait between site checks (in seconds)
  step: 60
  # Color of discord embed
  color: 0xFF5733
  # Skip reading last change from file
  # Set this to true if bot was offline for long time
  skip: false
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

if os.path.isfile('lastchange.json') == False:
    rasprint('File lastchange.json not found')
    rasprint('Creating file lastchange.json...')
    lastchange = {}
    with open('lastchange.json', 'x') as f:
        f = f.write(json.dumps(lastchange))

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
# Create dictionary to store data collected from webpage for each shift
# while bot is running
mega_dict_old_A = {}
mega_dict_old_B = {}
# Set first run variable to True
first_run = True
# Notify debug, send last changes to all servers manually
dnotify_B = False
dnotify_A = False
# Set embed color for bot
embed_color = config['settings']['color']
# Debbug mode variable
debug_mode = False
# Classroms changes disctionary
classrooms = {}

def site_check(shift: str, debug = False):
    shift = shift.upper()
    # Debug mode
    if(debug):
        rasprint('Run {} starting'.format(shift))
    # Create variables
    mega_dict = {}

    # Make reguest and get data from the site
    try:
        source = requests.get('https://tsrb.hr/{}-smjena/'.format(shift.lower())).text
    except:
        rasprint("Error occurred while getting data from site {}, skipping...".format(shift))
        return -1

    # Convert data to html code
    soup = BeautifulSoup(source, 'lxml')
    # Find iframes in the code
    tables = soup.find_all('iframe')
    # If there is no iframe print error and skip
    if(tables == None):
        rasprint("Can't get table link from site {}, skipping...".format(shift))
        return -1
    # find right iframe link in list
    for table in tables:
        tlink = table.attrs
        if 'docs.google.com' in tlink['src']:
            tablelink = tlink['src']

    # Get table code from iframe attribute
    try:
        newsource = requests.get(tablelink).text
    except:
        rasprint("Error occurred while getting data from iframe link {}, skipping...".format(shift))
        return -1
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
            mega_dict['titles'][str(control)] = span.text
            control = control + 1

    mega_dict['tables'] = {}
    classrooms = {}
    control = -1
    table_count = 0
    title_count = 0

    # Get data for each class from each table
    for table in soup.find_all('table'):
        mega_dict['tables'][str(table_count)] = {}
        # Check if shift is poslije podne
        poslijepodne = False
        for span in table.find_all('span'):
            if(span.text.startswith('-1')):
                poslijepodne = True
        # Check if table is for students
        shift_check = table.find('span').text.upper().startswith('PRIJE') or table.find('span').text.upper().startswith('POSLIJE')

        # Store table shift (Prije podne / Poslije podne) in dictonary
        if(shift_check and poslijepodne):
            mega_dict['tables'][str(table_count)]['shift'] = 'POSLIJE PODNE'
        elif(shift_check):
            mega_dict['tables'][str(table_count)]['shift'] = 'PRIJE PODNE'

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
                        mega_dict['tables'][str(table_count)][class_name][str(control)] += ' ' + span.text

                if(control == 9):
                    control = -1
                if(control != -1):
                    control = control + 1
                # If one cell goes over two colloms set next hour to same value
                if(cell.attrs['colspan'] != '1'):
                    for genius in range(2, int(cell.attrs['colspan']) + 1):
                        mega_dict['tables'][str(table_count)][class_name][str(control)] = ' ' + span.text
                        control = control + 1

        # If data in table is vaild move the counter
        if(bool(mega_dict['tables'][str(table_count)])):
            table_count = table_count + 1

            classroomst = ''
            par = table.next_sibling
            while True:
                if par.name != 'p' or par == None:
                    break
                if par.text.strip().startswith('RAS'):
                    break
                for span in par.find_all('span'):
                    if span.text.replace(' ', '') != '':
                        classroomst += re.sub('\s\s+', '\n', span.text)
                classroomst += '\n'
                par = par.next_sibling
            classrooms[mega_dict['titles'][str(title_count)]] = re.sub('\s\s+', '\n', re.sub(r'\n\s*\n', '\n', classroomst))
            title_count += 1
            
    # Convert data from dictionary to strings
    mega_dict_temp = {}
    for table_num, table in mega_dict['tables'].items():
        # Check if table is empty
        if(bool(table)):
            # If shift is Prije podne
            if(table['shift'] == 'PRIJE PODNE'):
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = {}
                        mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] = '```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] = '```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] += ' ' + hour + '. sat = ' + value.strip() + '\n'
                    mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] += '```'
            # If shift is Poslje podne
            else:
                for class_name, class_value in table.items():
                    # Skip shift keyword
                    if(class_name == 'shift'):
                        continue
                    # If class name is not in dict add it and set title
                    if(class_name not in mega_dict_temp):
                        mega_dict_temp[class_name] = {}
                        mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] = '```'
                    # Else set title
                    else:
                        mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] = '```'
                    # Add new line for each school hour
                    for hour, value in class_value.items():
                        if(int(hour) - 2 == -1):
                            mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] += str(int(hour) - 2) + '. sat = ' + value.strip() + '\n'
                        else:
                            mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] += ' ' + str(int(hour) - 2) + '. sat = ' + value.strip() + '\n'
                    # End discord code block
                    mega_dict_temp[class_name][mega_dict['titles'][table_num] + '\n' + table['shift']] += '```'

    # Set mega_dict to converted values
    mega_dict = dict(mega_dict_temp)
    
    # Debug mode
    if(debug):
        rasprint('Run {} finished'.format(shift))
    
    class result:
        def __init__(self):
            self.classrooms = classrooms
            self.dict = mega_dict

    # Return dictionary
    return result()

# Get input from console
@tasks.loop()
async def console_input():
    global debug_mode
    global dnotify_A
    global dnotify_B
    global client
    while True:
        value = await ainput()
        if(value == 'dlist'):
            i = 0
            rasprint('List of servers in database:')
            for k in data.keys():
                i += 1
                rasprint('- ' + data[k]['name'])
            rasprint('All (' + str(i) + ')')
        if(value == 'list'):
            i = 0
            rasprint('List of servers where bot is in:')
            for server in client.guilds:
                i += 1
                rasprint('- ' + server.name)
            rasprint('All (' + str(i) + ')')

        if(value == 'debug on'):
            debug_mode = True
            rasprint('Debug mode on')
        if(value == 'debug off'):
            debug_mode = False
            rasprint('Debug mode off')
        if(value == 'notify a'):
            rasprint('Sending last change to all configured servers in A shift')
            dnotify_A = True
        if(value == 'notify b'):
            rasprint('Sending last change to all configured servers in B shift')
            dnotify_B = True
        if(value == 'help'):
            rasprint('List of available commands:')
            rasprint('list - List all servers where bot is in')
            rasprint('dlist - list all servers from database')
            rasprint('debug on - enter debug mode')
            rasprint('debug off - exit debug mode')
            rasprint('notify a - send last changes to all configured servers in A shift')
            rasprint('notify b - send last changes to all configured servers in B shift')

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
    # Start loops if they are not running
    if not notify_loop.is_running():
        notify_loop.start()
    if not console_input.is_running():
        console_input.start()
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
@tasks.loop(seconds = config['settings']['step'])
async def notify_loop():

    global debug_mode
    if debug_mode:
        rasprint("Notify loop started")
    
    global first_run
    global dnotify_A
    global dnotify_B
    global mega_dict_old_A
    global mega_dict_old_B
    global lastchange
    global config
    global classrooms

    loop = asyncio.get_event_loop()
    mega_class_A = await loop.run_in_executor(None, site_check, 'A', debug_mode)
    loop = asyncio.get_event_loop()
    mega_class_B = await loop.run_in_executor(None, site_check, 'B', debug_mode)

    if mega_class_A != -1:
        mega_dict_A = mega_class_A.dict
        classrooms['A'] = mega_class_A.classrooms
    else:
        mega_dict_A = -1
        
    if mega_class_B != -1:
        mega_dict_B = mega_class_B.dict
        classrooms['B'] = mega_class_B.classrooms
    else:
        mega_dict_B = -1

    if(first_run):
        # Read last change from file
        with open('lastchange.json', 'r') as f:
            lastchange_f = f.read()
            lastchange = json.loads(lastchange_f)
        # If there was no file set last change to current schedule
        if lastchange == {} or config['settings']['skip']:
            lastchange['A'] = dict(mega_dict_A)
            lastchange['B'] = dict(mega_dict_B)
        # Set mega dicts old to last change
        mega_dict_old_A = dict(lastchange['A'])
        mega_dict_old_B = dict(lastchange['B'])
        # Write changes to file
        with open('lastchange.json', 'w') as f:
            f.write(json.dumps(lastchange))
        # Report that first run is finished
        first_run = False
        rasprint('Finished first run successfully')

    # Check if changes are made in A shift
    if((mega_dict_A != mega_dict_old_A or dnotify_A) and mega_dict_A != -1):
        if not dnotify_A:
            rasprint('Changes has been made in A shift')
        # Send changes to all A shift servers in database
        for server in client.guilds:
            # Skip server if not configured or not in A shift
            if data[str(server.id)]['channel_id'] != None and data[str(server.id)]['class'] != None and data[str(server.id)]['class'][2] in A_classes:
                # Check if changes are made for this class
                if(mega_dict_old_A[data[str(server.id)]['class']] != mega_dict_A[data[str(server.id)]['class']] or dnotify_A):
                    channel = client.get_channel(data[str(server.id)]['channel_id'])
                    embed=discord.Embed(
                        title="Izmjene u rasporedu " + data[str(server.id)]['class'],
                        url='https://www.tsrb.hr/a-smjena/',
                        color = embed_color)
                    for k, v in mega_dict_A[data[str(server.id)]['class']].items():
                        embed.add_field(name = k, value = v, inline = False)
                    try:
                        await channel.send(embed=embed)
                    except discord.errors.Forbidden:
                        rasprint("Don't have right permissions in server: {}".format(data[str(server.id)]['name']))
        # Set old list to new one after everyone are notified
        mega_dict_old_A = dict(mega_dict_A)
        # Store last change to file
        lastchange['A'] = dict(mega_dict_A)
        with open('lastchange.json', 'w') as f:
            f.write(json.dumps(lastchange))

        # Set notify variable back to false
        dnotify_A = False

    # Check if changes are made in B shift
    if((mega_dict_B != mega_dict_old_B or dnotify_B) and mega_dict_B != -1):
        if not dnotify_B:
            rasprint('Changes has been made in B shift')
        # Send changes to all B shift servers in database
        for server in client.guilds:
            # Skip server if not configured or not in B shift
            if data[str(server.id)]['channel_id'] != None and data[str(server.id)]['class'] != None and data[str(server.id)]['class'][2] in B_classes:
                # Check if changes are made for this class
                if(mega_dict_old_B[data[str(server.id)]['class']] != mega_dict_B[data[str(server.id)]['class']] or dnotify_B):
                    channel = client.get_channel(data[str(server.id)]['channel_id'])
                    embed=discord.Embed(
                        title="Izmjene u rasporedu " + data[str(server.id)]['class'],
                        url='https://www.tsrb.hr/b-smjena/',
                        color = embed_color)
                    for k, v in mega_dict_B[data[str(server.id)]['class']].items():
                        embed.add_field(name = k, value = v, inline = False)
                    try:
                        await channel.send(embed=embed)
                    except discord.errors.Forbidden:
                        rasprint("Don't have right permissions in server: {}".format(data[str(server.id)]['name']))
        # Set old list to new one after everyone are notified
        mega_dict_old_B = dict(mega_dict_B)
        # Store last change to file
        lastchange['B'] = dict(mega_dict_B)
        with open('lastchange.json', 'w') as f:
            f.write(json.dumps(lastchange))
        # Set notify variable back to false
        dnotify_B = False

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
    

def get_data(class_name, megadictA, megadictB):
    A_classes = {'A', 'B', 'C', 'D', 'O'}
    B_classes = {'E', 'F', 'G', 'M', 'N'}
    if(class_name in A_classes):
        data = megadictA[class_name]
    if(class_name in B_classes):
        data = megadictB[class_name]
    return data

# Add command raspored to send last changes, for class defined in database, or specified as command attribute
@client.command(aliases = ['ras', 'r'])
async def raspored(ctx, name = None):
    # Send error if first run is not done yet
    if(first_run):
        embed = discord.Embed(title = 'ZAHTJEV ODBIJEN', description = 'Pričekaj, povlačim podatke sa stranice\n ovo može potrajati do 30 s', color = embed_color)
    # If command has no argument and is send in server
    elif(name == None and ctx.guild != None):
        server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
        # If class is configured in that server
        if(data[str(server_id)]['class'] != None):
            class_name = data[str(server_id)]['class']
            if class_name[2] in A_classes:
                embed = discord.Embed(title = "Izmjene u rasporedu " + class_name, url = 'https://www.tsrb.hr/a-smjena/', color = embed_color)
                for k, v in mega_dict_old_A[class_name].items():
                    embed.add_field(name = k, value = v, inline = False)
            if class_name[2] in B_classes:
                embed = discord.Embed(title = "Izmjene u rasporedu " + class_name, url = 'https://www.tsrb.hr/b-smjena/', color = embed_color)
                for k, v in mega_dict_old_B[class_name].items():
                    embed.add_field(name = k, value = v, inline = False)
        # If class is not configured set embed to an error
        else:
            embed = discord.Embed(title = "Razred nije definiran", description = "Kako bi ste koristili ovu komandu potrebno je definirati razred", color = embed_color)
            embed.add_field(name = 'Definirajte razred (Admin)', value = '```.conf raz <ime razreda>```', inline = False)
            embed.add_field(name = 'Napišite željeni razred u komandi', value = '```.raspored <ime razreda>```', inline = False)
    # If there is no argument and command was send in PM, set embed to an error
    elif(name == None and ctx.guild == None):
        embed = discord.Embed(title = "Razred nije definiran", description = "Kako bi ste koristili bota u privatnim porukama potrebno je definirati razred.", color = embed_color)
        embed.add_field(name = 'Primjer', value = '```.raspored <ime razreda>```', inline = False)
    # If there is class as argument
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
                embed = discord.Embed(title = "Izmjene u rasporedu " + name, url = 'https://www.tsrb.hr/a-smjena/', color = embed_color)
                for k, v in mega_dict_old_A[name].items():
                    embed.add_field(name = k, value = v, inline = False)
            if name[2] in B_classes:
                embed = discord.Embed(title = "Izmjene u rasporedu " + name, url = 'https://www.tsrb.hr/b-smjena/', color = embed_color)
                for k, v in mega_dict_old_B[name].items():
                    embed.add_field(name = k, value = v, inline = False)
    await ctx.send(embed=embed)

@client.command(aliases = ['u', 'uc'])
async def ucionice(ctx, shift = None):
    if(first_run):
        embed = discord.Embed(title = 'ZAHTJEV ODBIJEN', description = 'Pričekaj, povlačim podatke sa stranice\n ovo može potrajati do 30 s', color = embed_color)
    elif(shift != None):
        if(shift.upper() == 'A' or shift.upper() == 'B'):
            embed = discord.Embed(
                title = 'Izmjene u učionicama ' + shift.upper() + ' smijena',
                description = 'Napomena: ova funkcija još nije potpuno stabilna.',
                color = embed_color)
            for k, v in classrooms[shift.upper()].items():
                embed.add_field(name = k, value = '```' + v + '```', inline = False)
        else:
            embed = discord.Embed(title = 'Smjena nije definirana', description = 'Molim upišite valjanu smjenu (A ili B)\nPrimjer: `.ucionice B`', color = embed_color)
    elif(ctx.guild == None and shift == None):
        embed = discord.Embed(title = 'Smjena nije definirana', description = 'Molim upišite valjanu smjenu (A ili B)\nPrimjer: `.ucionice B`', color = embed_color)
    elif(ctx.guild != None):
        server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
        if(data[str(server_id)]['shift'] != None):
            embed = discord.Embed(
                title = 'Izmjene u učionicama ' + data[str(server_id)]['shift'] + ' smijena',
                description = 'Napomena: ova funkcija još nije potpuno stabilna.',
                color = embed_color)
            for k, v in classrooms[data[str(server_id)]['shift']].items():
                embed.add_field(name = k, value = '```' + v + '```', inline = False)
        else:
            embed = discord.Embed(title = 'Smjena nije definirana',
            description = 'Kako biste koristili ovu komandu bez da definirate smjenu pri izvršavanju komande, morate definirati razred za ovaj server\nPrimjer: `.conf raz <ime razreda>`',
            color = embed_color)
    await ctx.send(embed = embed)

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
        name = 'Raspored (Alias: .r .ras)',
        value = '```.raspored```\nOva komanda ispisat će posljednje izmjene u rasporedu za razred definiran pri konfiguraciji, te se neće izvršiti ukoliko razred nije definiran.',
        inline = False
    )
    embed.add_field(
        name = 'Raspored za razred (Private) (Alias: .r .ras)',
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
        sleep(2)
