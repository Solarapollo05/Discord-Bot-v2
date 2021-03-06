import discord
from discord.ext.commands.errors import ExtensionFailed
#FIXME: Add improved error handling @logging
from discord.ext import commands, tasks
import linecache as lc
import sys, json, random, datetime, time, os
import logging #TODO: Add command logging (user, channel, server, time)

os.chdir(os.path.realpath(__file__)[0:-7]) # Change working directory to where this file is located

# --------------- Constants --------------- 
CUSTOM_PREFIX = False
CUSTOM_STATUS = False

logger_discord = logging.getLogger('discord') # Create logger for discord related messages

if len(sys.argv) > 1: # Set logging level to debug is program is run with -d or --debug option
    if sys.argv[1] == '-d' or sys.argv[1] == '--debug':
        logger_discord.setLevel(logging.DEBUG)
        print("Debugging enabled.")
else:
    logger_discord.setLevel(logging.INFO)

# --------------- Logging setup --------------- 

handler_discord = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler_discord.setFormatter(logging.Formatter('%(levelname)s %(asctime)s - %(message)s', datefmt='%d-%b-%Y %H:%M:%S'))
logger_discord.addHandler(handler_discord)
timestamp = str(datetime.datetime.now().strftime('%d-%m-%y-%H:%M'))
logger_discord.info(f"Log created at {time}")

logger_client = logging.getLogger('client') # Create logger for custom messages
logger_client.setLevel(logging.INFO)
handler_client = logging.FileHandler(filename='client.log', encoding='utf-8', mode='w')
handler_client.setFormatter(logging.Formatter('%(levelname)s %(asctime)s - %(message)s', datefmt='%d-%b-%Y %H:%M:%S'))
logger_client.addHandler(handler_client)
timestamp = str(datetime.datetime.now().strftime('%d-%m-%y-%H:%M'))
logger_client.info(f"Log created at {time}")

# --------------- Config File ---------------

class ConfigError(Exception):
    '''Error in provided config file.'''
    # TODO: Log errors in config file @logging

try: # Load config file, and report error if necessary
    CONFIG = json.load(open('Cogs/config.json', 'r'))
except json.decoder.JSONDecodeError as exception:
    config_error = bool(True)
    raise ConfigError('Unable to parse config file')


global default_prefix
if CONFIG['custom_prefix']['default'] == '': # Load prefix from config file
    default_prefix = '!'
else:
    default_prefix = str(CONFIG['custom_prefix']['default'])
    CUSTOM_PREFIX = True

def auth_owner(CONFIG, context): # Subprogram to authenticate owner as message author
    owner_username = CONFIG['owner']['username']
    owner_discriminator = CONFIG['owner']['discriminator']

    author_username = context.author.name
    author_discrim = context.author.discriminator
    
    try:
        if owner_username == author_username and owner_discriminator == author_discrim:
            owner = True
        else:
            owner = False
        return bool(owner)
    except:
        context.send('Error in configuration file. Unable to validate owner.')
        try:
            raise ConfigError('Error with owner details in config file')
            #TODO: Log error @logging
        except ConfigError as ex:
            print(ex)
        return bool(False)

def get_prefix(client, message): # Load Per server prefix
    if bool(CONFIG['custom_prefix']['enable']) == True:
        with open('Media/prefixes.json', 'r') as prefix_file:
            prefixes = json.load(prefix_file)
        return prefixes[str(message.guild.id)]
    else:
        return default_prefix

def random_status(): # Random playing status from Media/random_status.txt file
        for line in open('Media/random_status.txt', 'r').readlines():
            status_options = []
            status_options.append (str(line))
        chosen_status = random.choice(status_options)
        return chosen_status

bot = commands.Bot(command_prefix = get_prefix) #create bot
loaded_cogs = []

for cog in CONFIG['settings']['cogs']: #TODO use try and except to catch errors @logging
    try:
        bot.load_extension(f"Cogs.{cog}")
        loaded_cogs.append(cog)
        logger_client.info(f"{cog} loaded successfully")
    except:
        logger_client.warning(f"Failed to load {cog}")
        try:
            raise ExtensionFailed(cog, BaseException)
        except ExtensionFailed as e:
            logger_client.exception(f"An Error has occured\n{e}")


@bot.event
async def on_ready(): # Apply random status from text file unless a specific status is set
    if CONFIG['settings']['status'] == '':
        chosen_status = random_status()
        
    else:
        chosen_status = CONFIG['settings']['status']
        CUSTOM_STATUS = True
    await bot.change_presence(status=discord.Status.online)
    await bot.change_presence(activity=discord.Game(chosen_status))
    change_status.start() # Start random status loop

    print('Bot is Online!')
    global START_TIME
    START_TIME = time.time()

    logger_client.info(f'''
    ----- Begin Startup Message ----- 
Status: Playing {str(chosen_status)}
Loaded Cogs: {loaded_cogs}
Custom Prefixes Enabled: {bool(CONFIG['custom_prefix']['enable'])}
    Default Prefix : {CONFIG['custom_prefix']['default']}
Invite Enabled: {bool(CONFIG['invite']['enable'])}
    Permissions Integer: {CONFIG['invite']['permissions']}
Owner: {CONFIG['owner']['username']}#{CONFIG['owner']['discriminator']}
    ----- End Startup Message -----
''')
@bot.command() # Enable chosen cogs
async def load (ctx, cog_name):

    owner = bool(auth_owner(CONFIG, ctx))
    
    if owner == True:

        logger_client.info(f"{cog_name} loaded by owner.")

        try:
            bot.load_extension(f'Cogs.{cog_name}.py')
            loaded_cogs.append(cog_name)
            await ctx.reply(f'Loaded `{cog_name}.py`')
            
        except:
            await ctx.send(f'Failed to load `{cog_name}.py`')
            logger_client.warning(f"Failed to load {cog_name}.")

            try:
                raise ExtensionFailed(cog_name, BaseException) # Log error
            except ExtensionFailed as e:
                logger_client.exception(f"An error has occured:\n{e}")
    else:
        await ctx.send('Only the owner can use this command. If you are the owner, edit the values in config.json')
        logger_client.info(f"{ctx.author.name}{ctx.author.discriminator} attempted to use an admin command.")

@bot.command() # Disable chosen cogs

async def unload (ctx, cog_name):
      owner = bool(auth_owner(CONFIG, ctx))
      if owner == True:
        logger_client.info(f"unload {cog_name} requested by owner.")
        try:
            bot.unload_extension(f'Cogs.{cog_name}')
            loaded_cogs.remove(cog_name)
            await ctx.reply(f'Unloaded `{cog_name}.py`')
        except:
            await ctx.reply(f'Failed to unload `{cog_name}.py`.')
            logger_client.warning(f"Failed to unload {cog_name}")

            try:
                raise ExtensionFailed(cog_name, BaseException) # Report error
            except ExtensionFailed as e:
                logger_client.exception(f"An Error has occured:\n{e}")

      else:
          await ctx.send('Only the owner can use this command. This event will be logged. If you are the owner, edit the values in config.json')
          logger_client.info(f"{ctx.author.name}{ctx.author.discriminator} attempted to use an admin command.")

@bot.command() # Reload all cogs - update code without restarting bot
async def reload (ctx):
    owner = bool(auth_owner(CONFIG, ctx))
    if owner == True:
        logger_client.info("Attemting to  reload all cogs")
        try:
            for i in range(0, len(CONFIG['settings']['cogs'])):
                cog_name = CONFIG['settings']['cogs'][i]
                try:
                    bot.reload_extension(f'Cogs.{cog_name}')
                except: # Failed to load specific cog
                    await ctx.send(f'Failed to restart {cog_name}. The error has been logged.')
                    logger_client.warning(f"Failed to reload {cog_name}.")
                    loaded_cogs.remove(cog_name)


                    try:
                        raise ExtensionFailed(cog_name, BaseException) # Report error - need to pass params to exception
                    except ExtensionFailed as e:
                        logger_client.exception(f"An Error has occured:\n{e}")

            await ctx.send("Cogs reloaded")
        except: # Failed to read config file
            try:
                raise ConfigError('Failed to find enabled cogs in config file.')

            except ConfigError as e:
                
                logging.exception(f"An error has occured in the configuration file:\n{e}")
        await ctx.send("All cogs reloaded successfully.")

    else:
        await ctx.send('Only the owner can use this command. This event will be logged. If you are the owner, edit the values in config.json')
        logger_client.info(f"{ctx.author.name}{ctx.author.discriminator} attempted to use an admin command.")

@bot.command()
async def status(ctx):
    uptime = str(datetime.timedelta(seconds=int((round(time.time() - START_TIME)))))
    cogs = ""
    for cog in loaded_cogs:
        cogs = f"`{cog}`,\n{cogs}"

    with open('Media/prefixes.json', 'r') as prefix_file:
            prefixes = json.load(prefix_file)

    server_prefix = f"`{prefixes[str(ctx.guild.id)]}`"

    embed=discord.Embed(title="Current Status", description="*Current Status of the Discord Bot*", color=0xff0000)
    embed.add_field(name="Uptime:", value=uptime, inline=False)
    embed.add_field(name="Loaded Cogs:", value=cogs, inline=False)
    embed.add_field(name="Server Prefix:", value=server_prefix, inline=False)
    
    await ctx.send(embed=embed)


if str(CONFIG['settings']['token']) == '': # If there is no token in config file, use token file
    token = lc.getline('Media/token', 1)
else:
    try:
        token = str(CONFIG['settings']['token'])
    except:
        try:
            raise ConfigError('No token provided in config or token file.')
        except ConfigError as ex:
            print(ex)
            logger_client.exception(f"Warning - Exception Occured:\n{ex}")

@tasks.loop(minutes=30)
async def change_status():
    if CUSTOM_STATUS == False:
        new_status = random_status()
        await bot.change_presence(activity=discord.Game(new_status))
        logger_client.info(f"Status updated to {new_status}")

bot.run(token)
