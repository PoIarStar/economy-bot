from disnake.ext import commands
from configparser import ConfigParser

import psycopg2
import disnake
import os


class Bot1(commands.Bot):
    def __del__(self):
        conn.close()


config = ConfigParser()
config.read('config.ini')

conn = psycopg2.connect(
    dbname=config['database']['name'],
    user=config['database']['user'],
    password=config['database']['password'],
    host=config['database']['host'],
    port=config['database']['port'])

cur = conn.cursor()

bot = Bot1(command_prefix=disnake.ext.commands.when_mentioned,
           test_guilds=[971007825218240532],
           command_sync_flags=commands.CommandSyncFlags(),
           intents=disnake.Intents.all())

for name in os.listdir('cogs'):
    if name.endswith('.py'):
        bot.load_extension(f'cogs.{name[:-3]}')

bot.run(config['bot']['token'])
