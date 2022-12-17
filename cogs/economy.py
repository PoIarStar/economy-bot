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
                        f"('{emoji}', '{name}', {bool(is_crypt)}, {system}, {0 if is_crypt else None},"
                        f" {0 if is_crypt else None})")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError:
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def edit_currency(self, inter, name, new_name, emoji):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"UPDATE currency SET emoji = '{emoji}', name = '{new_name}' WHERE"
                        f" name = '{name}' AND system = {system}")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError:
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def delete_currency(self, inter, currency):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT * FROM currency WHERE system = {system}")
            if cur.fetchone():
                cur.execute(f"DELETE FROM currency WHERE system = {system} and name = '{currency}'")
                conn.commit()
                await inter.response.send_message('Успешно')
            else:
                await inter.response.send_message('Данной валюты не существует')
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
                text += (f'[{c}] {i[4]} ' + i[0] +
                         (', ходовая валюта' if not i[1] else ', криптовалюта, ' +
                                                              f'в ходу: {i[2]}, ' + f'свободно: {i[3]}') + '\n')
                c += 1
            await inter.response.send_message(embed=disnake.Embed(title='Валюты', description=text))
        except TypeError:
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def profile(self, inter, user: disnake.Member):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT lvl, xp, social_rating, work_id, currency_1, currency_2, currency_3, currency_4, "
                        f"currency_5 FROM users WHERE system = {system} AND uid = {user.id}")
            values = cur.fetchone()
            values, currencies = values[:4], values[4:]
            cur.execute(f'SELECT emoji, name, id FROM currency WHERE system = {system} ORDER BY id')
            balance = cur.fetchall()
            text = f'Баланс:\n'
            for i in balance:
                text += f'•\t{i[1]}: {currencies[i[2] - 1]}{i[0]}\n'
            text += f'Уровень: {values[0]}({values[1]}/{values[0] * 25})\n'
            cur.execute(f'SELECT name FROM works WHERE id = {values[3] if values[3] else 0} and system = {system}')
            work = cur.fetchone()
            text += f'Работа: {work[0] if work else "нет"}\n'
            text += f'Уровень доверия: {(values[2] + 3) // 4}'
            embed = disnake.Embed(title='Профиль', description=text, color=user.colour)
            embed.set_author(name=(user.nick if user.nick else user.name), url=f'https://discordapp.com/users/{user.id}', icon_url=user.avatar.url)
            await inter.response.send_message(embed=embed)
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')


def setup(bot):
    bot.add_cog(Economy(bot))
