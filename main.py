from disnake.ext import commands
from config import settings
import psycopg2
import disnake
import os


conn = psycopg2.connect(
    dbname='bot',
    user='postgres',
    password=settings['passwd'],
    host='127.0.0.1',
    port=5432)

cur = conn.cursor()


bot = commands.Bot(command_prefix=disnake.ext.commands.when_mentioned,
                   test_guilds=[983432883714789476],
                   sync_commands_debug=True,
                   intents=disnake.Intents.all())

for name in os.listdir("cogs"):
    if name.endswith(".py"):
        bot.load_extension(f"cogs.{name[:-3]}")

bot.run(settings["token"])
