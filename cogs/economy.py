from disnake.ext import commands
from main import cur, conn
import disnake


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Economy succesfully loaded')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_currency(self, inter, name, emoji, is_crypt=False):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"INSERT INTO currency(emoji, name, is_crypt, system, in_use, free) VALUES "
                        f"('{emoji}', '{name}', {bool(is_crypt)}, {system}, {0 if is_crypt else None}, {0 if is_crypt else None})")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError:
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def currencies(self, inter):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT name, is_crypt, in_use, free, emoji FROM currency WHERE system = {system}")
            currencies = cur.fetchall()
            text = ''
            c = 1
            for i in currencies:
                text += (f'[{c}] {i[4]} ' + i[0] + (', ходовая валюта' if not i[1] else ', криптовалюта, ' + f'в ходу: {i[2]}, ' + f'свободно: {i[3]}') + '\n')
                c += 1
            await inter.response.send_message(embed=disnake.Embed(title='Валюты', description=text))
        except TypeError:
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')


def setup(bot):
    bot.add_cog(Economy(bot))
