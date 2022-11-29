from disnake.ext import commands
from main import cur, conn


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Economy succesfully loaded')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_currency(self, inter, name, is_crypt=False):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        system = cur.fetchone()[0]
        cur.execute(f"INSERT INTO currency(name, is_crypt, system) VALUES ('{name}', {bool(is_crypt)}, {system})")
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.slash_command()
    async def currencies(self, inter):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        system = cur.fetchone()[0]
        cur.execute(f"SELECT name, is_crypt, in_use, free FROM currency WHERE system = {system}")
        currencies = cur.fetchall()
        text = ''
        for i in currencies:
            text += (i[0] + (', ходовая валюта' if not is_crypt else ', криптовалюта, ' + f'в ходу: {}, ' + f'свободно: {}'))
        emb = disnake.Embed(title='Валюты', description=text)
        await inter.response.send_message(embed=emb)


def setup(bot):
    bot.add_cog(Economy(bot))
