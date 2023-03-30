from disnake.ext import commands
from main import cur, conn
from time import time
from random import choice
from config import default
import disnake


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_currency(self, inter, name, emoji, is_crypt=False):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT id FROM currency WHERE system = {system}")
            ids = [i[0] for i in cur.fetchall()]
            if len(ids) > 4:
                await inter.response.send_message('Достигнуто максимальное количество валют')
                return
            cur.execute(f"INSERT INTO currency(emoji, name, is_crypt, system, in_use, free, id) VALUES "
                        f"('{emoji}', '{name}', {bool(is_crypt)}, {system}, {0 if is_crypt else 'NULL'},"
                        f" {0 if is_crypt else 'NULL'}, {min(i for i in range(1, 6) if i not in ids)})")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError as e:
            print(e)
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
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def delete_currency(self, inter, currency):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT * FROM currency WHERE system = {system}")
            if cur.fetchone():
                cur.execute(f"SELECT id FROM currency WHERE name = '{currency}' and system = {system}")
                num = cur.fetchone()[0]
                cur.execute(f"UPDATE users SET currency_{num} = 0 WHERE system = {system}")
                cur.execute(f"DELETE FROM currency WHERE system = {system} and name = '{currency}'")
                conn.commit()
                await inter.response.send_message('Успешно')
            else:
                await inter.response.send_message('Данной валюты не существует')
        except TypeError as e:
            print(e)
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
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def profile(self, inter, user: disnake.User):
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
            embed.set_author(name=user.name,
                             url=f'https://discordapp.com/users/{user.id}', icon_url=user.avatar.url)
            await inter.response.send_message(embed=embed)
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_work(self, inter, name, currency, wages, requirement_level):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"INSERT INTO works(name, currency, wages, req_lvl, system) VALUES"
                        f" ('{name}', '{currency}', {wages}, {requirement_level}, {system})")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def add_money(self, inter, user: disnake.User, currency, value, reason='не указана'):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT id FROM currency WHERE name = '{currency}' and system = {system}")
            num = cur.fetchone()[0]
            cur.execute(f"UPDATE users set currency_{num} = currency_{num} + {int(value)} WHERE uid = {user.id} "
                        f"AND system = {system}")
            conn.commit()
            await inter.response.send_message(f'{user} получает {value} единиц валюты {currency}. Причина: {reason}')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def works(self, inter):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT name, req_lvl, currency, wages FROM works WHERE system = {system}")
            emb = disnake.Embed(title='Вакансии')
            for i in cur.fetchall():
                emb.add_field(i[0], f'Необходимый уровень: {i[1]}\nВалюта оплаты: {i[2]}\nОплата: {i[3]}')
            await inter.response.send_message(embed=emb)
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def work_selection(self, inter, name):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT id FROM works WHERE system = {system} and name = '{name}'")
            work = cur.fetchone()
            if not work:
                await inter.response.send_message('Вакансии с таким названием не существует')
                return
            cur.execute(f"SELECT lvl FROM users WHERE system = {system} and uid = {inter.author.id}")
            lvl = cur.fetchone()[0]
            cur.execute(f"SELECT req_lvl FROM works WHERE system = {system} and name = '{name}'")
            if cur.fetchone()[0] > lvl:
                await inter.response.send_message('У вас слишком низкий уровень')
                return
            cur.execute(f'UPDATE users SET work_id = {work[0]} WHERE system = {system} and uid = {inter.author.id}')
            conn.commit()
            await inter.response.send_message(f'Вы успешно устроились на работу по профессии {name}')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    async def work(self, inter):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT work_time, work_id FROM users WHERE system = {system} and uid = {inter.author.id}")
            timer, work = cur.fetchone()
            time_now = time()
            if time_now < timer:
                await inter.response.send_message(f'Вы можете работать <t:{timer}:R>')
                return
            elif not work:
                await inter.response.send_message(f'Вы не устроены на работу')
                return
            while timer < time_now:
                timer += 86400
            cur.execute(f"UPDATE users SET work_time = {timer} WHERE system = {system} and uid = {inter.author.id}")
            conn.commit()
            cur.execute(f"SELECT wages, currency FROM works WHERE system = {system} and id = {work}")
            wages, currency = cur.fetchone()
            cur.execute(f"SELECT id, emoji FROM currency WHERE name = '{currency}' AND system = {system}")
            currency, emoji = cur.fetchone()
            cur.execute(f"UPDATE users SET currency_{currency} = currency_{currency} + {wages} WHERE system = {system}"
                        f" AND uid = {inter.author.id}")
            conn.commit()
            await inter.response.send_message(f'Вы заработали {wages}{emoji}')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_item(self, inter, name, description, currency, price: int, add_role: disnake.Role = None,
                          remove_role: disnake.Role = None):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT id FROM currency WHERE system = {system} AND name = '{currency}'")
            currency = cur.fetchone()[0]
            cur.execute("INSERT INTO SHOP(name, description, currency, price, add_role, remove_role, guild)"
                        f" VALUES('{name}', '{description}', '{currency}', {price}, "
                        f"{add_role.id if add_role else 'NULL'}, {remove_role.id if remove_role else 'NULL'},"
                        f" {inter.guild.id})")
            conn.commit()
            await inter.response.send_message('Успешно')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def delete_item(self, inter, name):
        cur.execute(f"DELETE FROM shop WHERE name = '{name}' and guild = {inter.guild.id}")
        conn.commit()
        await inter.response.send_message('Если что-то с таким названием было, его больше нет')

    @commands.slash_command()
    async def shop(self, inter):
        cur.execute(f'SELECT system FROM guilds WHERE guild = {inter.guild.id}')
        system = cur.fetchone()[0]
        cur.execute(f"SELECT name, currency, price, add_role, remove_role, description FROM shop"
                    f" WHERE guild = {inter.guild.id}")
        emb = disnake.Embed(title='Магазин')
        for i in cur.fetchall():
            i = list(i)
            if system:
                cur.execute(f"SELECT name FROM currency WHERE id = {i[1]} AND system = {system}")
                i[1] = cur.fetchone()
            else:
                i[1], i[2] = choice(default), '∞'
            field = '\n'.join([i for i in ['**Стоимость:** ' + str(i[2]),
                                           ('**Валюта:** ' + str(i[1][0])) if i[1] not in default else '' + i[1],
                                           '**Добавляемая роль:** ' + f'<@&{i[3]}>' if i[3] else '',
                                           '**Снимаемая роль:** ' + f'<@&{i[4]}>' if i[4] else '',
                                           '**Описание:** ' + i[5]
                                           ] if i])
            emb.add_field(name=i[0], value=field, inline=False)
        await inter.response.send_message(embed=emb)

    @commands.slash_command()
    async def buy(self, inter, name):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        try:
            system = cur.fetchone()[0]
            cur.execute(f"SELECT price, currency, req_lvl, add_role, remove_role FROM shop"
                        f" WHERE guild = {inter.guild.id} AND name = '{name}'")
            item = cur.fetchone()
            if item:
                cur.execute(f'SELECT lvl FROM users WHERE uid = {inter.author.id} AND system = {system}')
                if cur.fetchone()[0] < item[2]:
                    await inter.response.send_message('Слишком низкий уровень')
                    return
                cur.execute(f'SELECT currency_{item[1]} FROM users WHERE uid = {inter.author.id} AND system = {system}')
                if cur.fetchone()[0] < item[0]:
                    await inter.response.send_message('Недостаточно средств')
                    return
                if item[3]:
                    await inter.author.add_roles(inter.guild.get_role(item[3]))
                if item[4]:
                    await inter.author.remove_roles(inter.guild.get_role(item[4]))
                cur.execute(f'UPDATE users SET currency_{item[1]} = currency_{item[1]} - {item[0]} WHERE'
                            f' uid = {inter.author.id} AND system = {system}')
                conn.commit()
                await inter.response.send_message('Успешно')
        except TypeError as e:
            print(e)
            await inter.response.send_message('Ваш сервер не подключен к экономической системе')


def setup(bot):
    bot.add_cog(Economy(bot))
