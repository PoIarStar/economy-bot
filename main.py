from disnake.ext import commands
from config import settings
import psycopg2
import disnake
import os


class Bot1(commands.Bot):
    def __del__(self):
        conn.close()


conn = psycopg2.connect(
    dbname='bot',
    user='postgres',
    password=settings['passwd'],
    host='127.0.0.1',
    port=5432)

cur = conn.cursor()

bot = Bot1(command_prefix=disnake.ext.commands.when_mentioned,
           test_guilds=[983432883714789476, 971007825218240532],
           sync_commands_debug=True,
           intents=disnake.Intents.all())

for name in os.listdir("cogs"):
    if name.endswith(".py"):
        bot.load_extension(f"cogs.{name[:-3]}")

bot.run(settings["token"])
