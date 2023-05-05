from disnake.ext import commands
from main import cur, conn
from time import time
from random import choice, randint
from dbtools import get_system, get_currency

import disnake
import json


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wheel = [
            20,
            *[10] * 3,
            *[5] * 6,
            *[1] * 30,
            *[0] * 48,
            *[-0.5] * 12,
            *[-0.9] * 60,
            *[-1] * 30
        ]

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_currency(self, inter, name, emoji, is_crypt=False):
        system = get_system(inter.guild.id)
        cur.execute(f"SELECT id FROM currencies WHERE system = {system}")
        ids = [i[0] for i in cur.fetchall()]
        if len(ids) > 4:
            await inter.response.send_message('Достигнуто максимальное количество валют')
            return
        cur.execute(f"INSERT INTO currencies(emoji, name, is_crypt, system, in_use, free, id) VALUES "
                    f"('{emoji}', '{name}', {bool(is_crypt)}, {system}, {0 if is_crypt else 'NULL'},"
                    f" {0 if is_crypt else 'NULL'}, {min(i for i in range(1, 6) if i not in ids)})")
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def edit_currency(self, inter, name, new_name, emoji):
        system = get_system(inter.guild.id)
        cur.execute(f"UPDATE currencies SET emoji = '{emoji}', name = '{new_name}' WHERE"
                    f" name = '{name}' AND system = {system}")
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def delete_currency(self, inter, currency: str = None):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(f"SELECT * FROM currencies WHERE system = {system}")
        if cur.fetchone():
            cur.execute(f"SELECT id FROM currencies WHERE name = '{currency}' and system = {system}")
            num = cur.fetchone()[0]
            cur.execute(f"UPDATE users SET currency_{num} = 0 WHERE system = {system}")
            cur.execute(f"DELETE FROM currencies WHERE system = {system} and name = '{currency}'")
            conn.commit()
            await inter.response.send_message('Успешно')
        else:
            await inter.response.send_message('Данной валюты не существует')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def default_currency(self, inter, id: int = 1):
        system = get_system(inter.guild.id)
        cur.execute(f'UPDATE systems SET default_currency = {id} WHERE id = {system}')
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.slash_command()
    async def currencies(self, inter):
        system = get_system(inter.guild.id)
        cur.execute(f"SELECT name, is_crypt, in_use, free, emoji FROM currencies WHERE system = {system}")
        currencies = cur.fetchall()
        text = ''
        c = 1
        for i in currencies:
            text += (f'[{c}] {i[4]} ' + i[0] +
                     (', ходовая валюта' if not i[1] else ', криптовалюта, ' +
                                                          f'в ходу: {i[2]}, ' + f'свободно: {i[3]}') + '\n')
            c += 1
        await inter.response.send_message(embed=disnake.Embed(title='Валюты', description=text))

    @commands.slash_command()
    async def profile(self, inter, user: disnake.User):
        system = get_system(inter.guild.id)
        cur.execute(f"SELECT lvl, xp, social_rating, work_id, currency_1, currency_2, currency_3, currency_4, "
                    f"currency_5 FROM users WHERE system = {system} AND uid = {user.id}")
        values = cur.fetchone()
        values, currencies = values[:4], values[4:]
        cur.execute(f'SELECT emoji, name, id FROM currencies WHERE system = {system} ORDER BY id')
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

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_work(self, inter, name, wages: int, requirement_level: int = 1, currency: str = None):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(f"INSERT INTO works(name, currency, wages, req_lvl, system) VALUES"
                    f" ('{name}', '{currency}', {wages}, {requirement_level}, {system})")
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def add_money(self, inter, user: disnake.User, value, currency: str = None, reason=''):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(f"UPDATE users set currency_{currency} = currency_{currency} + {int(value)} WHERE uid = {user.id} "
                    f"AND system = {system}")
        conn.commit()
        await inter.response.send_message(f'{user} получает {value} единиц валюты {currency}.'
                                          f' {f"Причина: {reason}" if reason else ""}')

    @commands.slash_command()
    async def works(self, inter):
        system = get_system(inter.guild.id)
        cur.execute(f"SELECT name, req_lvl, currency, wages FROM works WHERE system = {system}")
        emb = disnake.Embed(title='Вакансии')
        for i in cur.fetchall():
            emb.add_field(i[0], f'Необходимый уровень: {i[1]}\nВалюта оплаты: {i[2]}\nОплата: {i[3]}')
        await inter.response.send_message(embed=emb)

    @commands.slash_command()
    async def work_selection(self, inter, name):
        system = get_system(inter.guild.id)
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

    @commands.slash_command()
    async def work(self, inter):
        system = get_system(inter.guild.id)
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
        cur.execute(f"SELECT id, emoji FROM currencies WHERE name = '{currency}' AND system = {system}")
        currency, emoji = cur.fetchone()
        cur.execute(f"UPDATE users SET currency_{currency} = currency_{currency} + {wages} WHERE system = {system}"
                    f" AND uid = {inter.author.id}")
        conn.commit()
        await inter.response.send_message(f'Вы заработали {wages}{emoji}')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_item(self, inter, name, description, price: int, currency: str = None,
                          add_role: disnake.Role = None, remove_role: disnake.Role = None):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute("INSERT INTO SHOP(name, description, currency, price, add_role, remove_role, guild)"
                    f" VALUES('{name}', '{description}', '{currency}', {price}, "
                    f"{add_role.id if add_role else 'NULL'}, {remove_role.id if remove_role else 'NULL'},"
                    f" {inter.guild.id})")
        conn.commit()
        await inter.response.send_message('Успешно')

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
        recession = json.loads('datas.json')['recession']
        for i in cur.fetchall():
            i = list(i)
            if system:
                cur.execute(f"SELECT name FROM currencies WHERE id = {i[1]} AND system = {system}")
                i[1] = cur.fetchone()
            else:
                i[1], i[2] = choice(recession), '∞'
            field = '\n'.join([i for i in ['**Стоимость:** ' + str(i[2]),
                                           ('**Валюта:** ' + str(i[1][0])) if i[1] not in recession else '' + i[1],
                                           '**Добавляемая роль:** ' + f'<@&{i[3]}>' if i[3] else '',
                                           '**Снимаемая роль:** ' + f'<@&{i[4]}>' if i[4] else '',
                                           '**Описание:** ' + i[5]
                                           ] if i])
            emb.add_field(name=i[0], value=field, inline=False)
        await inter.response.send_message(embed=emb)

    @commands.slash_command()
    async def buy(self, inter, name):
        system = get_system(inter.guild.id)
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

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def set_death_role(self, inter, role: disnake.Role):
        cur.execute(f'UPDATE guilds SET dead_role = {role.id} WHERE guild = {inter.guild.id}')
        conn.commit()
        await inter.response.send_message('Успешно')

    @commands.cooldown(5, 1800)
    @commands.slash_command()
    async def roulette(self, inter, currency: str = None, bullets: int = 1):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        if bullets < 1:
            await inter.response.send_message(
                'Хотите гарантий, что не проиграете? Гарантирую, что вы не выиграете!'
            )
            return
        elif bullets > 6:
            await inter.response.send_message('Очень жаль, но револьвер шестизарядный.')
            return
        cur.execute(f'SELECT dead_role FROM guilds WHERE guild = {inter.guild.id}')
        role = cur.fetchone()
        if role:
            if role[0] in [i.id for i in inter.author.roles]:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title='Русская рулетка',
                        description='Мёртвым нельзя умирать. Иначе даже Бог вас не воскресит.'))
                return
        if randint(1, 6) > bullets:
            cur.execute(f"SELECT great_unit, emoji, id FROM currencies WHERE name = '{currency}'")
            currency = cur.fetchone()
            if not currency:
                await inter.response.send_message('Название валюты указано неверно')
                return
            unit, emoji, id = currency
            cur.execute(f'SELECT roulette_cnt FROM users WHERE uid = {inter.author.id} AND system = {system}')
            cnt = cur.fetchone()[0]
            prize = round(bullets * unit * cnt)
            cur.execute(
                f'UPDATE users SET currency_{id} = currency_{id} + {prize}'
                f' WHERE uid = {inter.author.id} AND system = {system}'
            )
            cur.execute(f'UPDATE users SET roulette_cnt = roulette_cnt + 0.1 '
                        f'WHERE uid = {inter.author.id} AND system = {system}')
            conn.commit()
            await inter.response.send_message(f'Поздравляю. Вы выиграли {prize}{emoji}')
        else:
            cur.execute(f'UPDATE users SET roulette_cnt = 1 '
                        f'WHERE uid = {inter.author.id} AND system = {system}')
            conn.commit()
            if role:
                await inter.author.add_roles(inter.guild.get_role(role[0]))
            await inter.response.send_message('Вы умерли. Соболезнуем вам и вашим близким')

    @commands.slash_command()
    @commands.cooldown(5, 3600, type=commands.BucketType.user)
    async def wheel_of_fortune(self, inter, bet: int, currency: str = None):
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(
            f"SELECT is_crypt, great_unit, id, emoji FROM currencies WHERE name = '{currency}' AND system = {system}")
        currency = cur.fetchone()
        if currency[0]:
            await inter.response.send_message('Мы не принимаем криптовалюту')
            return
        cur.execute(f'SELECT currency_{currency[2]} FROM users WHERE uid = {inter.author.id} and system = {system}')
        money = cur.fetchone()[0]
        if bet > 1000000 * currency[1]:
            await inter.response.send_message(
                embed=disnake.Embed(title='Колесо фортуны', description='Разорить нас хочешь?'))
        elif bet <= 0:
            await inter.response.send_message(
                embed=disnake.Embed(title='Колесо фортуны', description='Не пытайся обмануть систему.'))
        elif money >= bet:
            win = choice(self.wheel) * bet
            await inter.response.send_message(
                embed=disnake.Embed(
                    title='Колесо фортуны',
                    description=f'Вы выиграли {win + bet}{currency[3]}. С учётом ставки вы '
                                f'{"выиграли" if win > 0 else "проиграли"} {abs(win)}{currency[3]}'))
            cur.execute(f'UPDATE users SET currency_{currency[2]} = currency_{currency[2]} + {win} WHERE uid'
                        f' = {inter.author.id} AND system = {system}')
            conn.commit()
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title='Колесо фортуны', description='У вас не хватает денег'))


def setup(bot):
    bot.add_cog(Economy(bot))
