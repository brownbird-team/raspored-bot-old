#   ____                                    _   ____        _   
#  |  _ \ __ _ ___ _ __   ___  _ __ ___  __| | | __ )  ___ | |_ 
#  | |_) / _` / __| '_ \ / _ \| '__/ _ \/ _` | |  _ \ / _ \| __|
#  |  _ < (_| \__ \ |_) | (_) | | |  __/ (_| | | |_) | (_) | |_ 
#  |_| \_\__,_|___/ .__/ \___/|_|  \___|\__,_| |____/ \___/ \__|
#                 |_|                         

# Made by BrownBird team
# Discord bot used to look for daily schedule changes on tsrb.hr/b-smjena

# Bot version
ver = '2.1.2'

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
prRed("Version: " + ver)
prRed("Made by BrownBird Team\n")

# Create file config.yml if doesn't exist
if(os.path.isfile('config.yml') == False):
    print('config.yml not found')
    print('Creating config.yml ...')
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
    print('Please configure bot in config.yml and restart it')
    exit()

# Create file database.json if doesn't exist to store server data
if os.path.isfile('database.json') == False:
    print('File database.json not found')
    print('Creating file database.json...')
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
    print('There is no token in config file')
    exit()
# Print to console if test has passed
print('Config OK')

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

# Look for changes on site B
def site_check_B():
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
    source = requests.get('https://tsrb.hr/b-smjena/').text

    # Convert data to html code
    soup = BeautifulSoup(source, 'lxml')
    # Find iframe in the code
    table = soup.find('iframe')
    # If there is no iframe print error and skip
    if(table == None):
        print("Can't get table link from site B, skipping...")
        start = 1
        return
    tablelink = table.attrs

    # Get table code from iframe attribute
    newsource = requests.get(tablelink['src']).text
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
        print('Finished first run B, Ready')
    # If this is not first run compare old and new dict
    # If they are diffrent set old dict to new one and notify variable to 1
    elif(mega_dict != mega_dict_old_B):
        mega_dict_old_B = dict(mega_dict)
        notify_B = 1

    # Sleep for 2 sec and set start variable to 1 so watch thread will restart site check
    sleep(2)
    start_B = 1

# Look for changes on site A
def site_check_A():
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
    source = requests.get('https://tsrb.hr/a-smjena/').text

    # Convert data to html code
    soup = BeautifulSoup(source, 'lxml')
    # Find iframe in the code
    table = soup.find('iframe')
    # If there is no iframe print error and skip
    if(table == None):
        print("Can't get table link from site A, skipping...")
        start = 1
        return
    tablelink = table.attrs

    # Get table code from iframe attribute
    newsource = requests.get(tablelink['src']).text
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
        print('Finished first run A, Ready')
    # If this is not first run compare old and new dict
    # If they are diffrent set old dict to new one and notify variable to 1
    elif(mega_dict != mega_dict_old_A):
        mega_dict_old_A = dict(mega_dict)
        notify_A = 1

    # Sleep for 2 sec and set start variable to 1 so watch thread will restart site check
    sleep(2)
    start_A = 1

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
client = commands.Bot(command_prefix = config['settings']['bot_prefix'])
# Remove default help command
client.remove_command('help')

@client.event
# When bot is ready
async def on_ready():
    # Start loop to check notify variable
    my_loop.start()
    # Print info to console
    print('Connected to bot: {}'.format(client.user))
    print('Bot ID: {}'.format(client.user.id))
    # Set bot status
    await client.change_presence(
        activity=discord.Activity(type = discord.ActivityType.watching, name = 'for something'))
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
                    color = 0xFF5733)
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
                    color = 0xFF5733)
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
        embed = discord.Embed(title='Bot configuration', color = 0xFF5733)
        embed.add_field(name = '&conf name', value = 'Run this command in channel where you want to receve notifications.', inline = False)
        embed.add_field(name = '&conf raz <class name>', value = 'Set the class name, replace `<class name>` with yours.', inline = False)
        await ctx.send(embed = embed)

# Add conf subcommand channel, set channel in database to channel where command is issued
@conf.command()
async def channel(ctx):
    channel_id = discord.utils.get(ctx.guild.channels, name=str(ctx.channel)).id
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    data[str(server_id)]['channel_id'] = channel_id
    data[str(server_id)]['channel_name'] = str(ctx.channel)
    with open('database.json', 'w') as f:
        f.write(json.dumps(data))
    embed = discord.Embed(
        title = 'Notifications channel',
        description = 'Notifications channel has been set to **{}**,\n you will receve notifications here when schedule changes.'.format(str(ctx.channel)),
        color = 0xFF5733
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
        await ctx.send("Please set vaild class name (example: 2.G)")
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
        title = 'School Class',
        description = 'School class has been set to **{}** in **{}** shift, you will be informed when schedule changes for that school class.'.format(class_name, data[str(server_id)]['shift']),
        color = 0xFF5733
    )
    await ctx.send(embed = embed)

# Add conf subcommand status, Display information from database for your server
@conf.command()
async def status(ctx):
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    embed = discord.Embed(
        title = 'Configuration Status',
        color = 0xFF5733
    )
    embed.add_field(name = 'Class', value = '```' + str(data[str(server_id)]['class']) + '```', inline = True)
    embed.add_field(name = 'Shift', value = '```' + str(data[str(server_id)]['shift']) + '```', inline = True)
    embed.add_field(name = 'Notifications Channel', value = '```' + str(data[str(server_id)]['channel_name']) + '```', inline = False)
    await ctx.send(embed = embed)

# Add command raspored to send last changes, for class defined in database
@client.command()
@commands.guild_only()
async def raspored(ctx):
    server_id = discord.utils.get(client.guilds, name=str(ctx.guild)).id
    class_name = data[str(server_id)]['class']
    if(first_run_A == 0 or first_run_B == 0):
        embed = discord.Embed(title = 'ZAHTJEV ODBIJEN', description = 'Pričekaj, povlačim podatke sa stranice\n ovo može potrajati do 20 s', color = 0xFF5733)
    else:
        if data[str(server_id)]['class'][2] in A_classes:
            description = mega_dict_old_A[data[str(server_id)]['class']]
        else:
            description = mega_dict_old_B[data[str(server_id)]['class']]
        embed = discord.Embed(title = "Raspored " + class_name, url = 'https://www.tsrb.hr/b-smjena/', description = description, color = 0xFF5733)
    await ctx.send(embed=embed)

# Add a version command to display bot version
@client.command()
async def version(ctx):
    await ctx.send(
        'Koristite **Raspored Bot** verzija **' + ver + '**\nMade by BrownBird Team'
    )

@raz.error
async def raz_error(ctx, error):
    # Send error message when class in not specified after raz command
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("Please specify school class")

@conf.error
async def conf_error(ctx, error):
    # Send error message if non admin try to execute command
    if isinstance(error, discord.ext.commands.errors.MissingPermissions):
        await ctx.send("You don't have a permission to execute that command")
    # Send error message if executed as private message
    if isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send("This command can't be used in private messages")

@raspored.error
async def raspored_error(ctx, error):
    # Send error message if executed as private message
    if isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
        await ctx.send("This command can't be used in private messages")

    
# Run client with token form config.yml
client.run(config['settings']['token'])
