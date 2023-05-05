import disnake
from disnake.ext import commands
from main import cur, conn
from datas import bank
from dbtools import get_system, get_currency

import time


class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Получение пользователем кредита
    @commands.slash_command()
    async def get_credit(self, inter, money: int, days: int, currency: str = None):
        cur.execute(f"SELECT * FROM bank WHERE uid = {inter.author.id}")
        if money <= 0:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У нас серьёзное заведение, а не цирк.'))
            return
        elif cur.fetchone() is not None:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк',
                                    description='Вы не можете выполнять несколько операций '
                                                'в нашем банке одновременно.'))
            return
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(f"SELECT is_crypt, great_unit, id, emoji, name FROM currencies "
                    f"WHERE name = '{currency}' and system = {system}")
        currency = cur.fetchone()
        if not currency:
            await inter.response.send_message('Название валюты указано неверно')
            return
        if currency[0]:
            await inter.response.send_message('Мы не выдаём кредиты в криптовалюте')
            return
        cur.execute(f'SELECT social_rating, guarantor, work_id FROM users '
                    f'WHERE uid = {inter.author.id} AND system = {system}')
        rating, guarantor, work = cur.fetchone()
        if not work:
            await inter.response.send_message('Мы не выдаём кредиты безработным.')
            return
        if guarantor:
            cur.execute(f'SELECT social_rating FROM users WHERE uid = {guarantor}')
            guarantor_rating = cur.fetchone()[0]
        else:
            guarantor_rating = 0
            guarantor = inter.author.id
        rating = (rating + 3) // 4
        if rating > 5:
            rating = 5
        if money <= 10 ** (2 + max(rating, guarantor_rating)) * currency[1]:
            cur.execute(f'SELECT wages FROM works WHERE id = {work}')
            wages = cur.fetchone()[0]
            if days < money // wages + 1 and days < 29:
                cur.execute(
                    f"INSERT INTO bank(system, uid, currency, value, rate, reg_time, end_time, type, guarantor) VALUES "
                    f"({system}, {inter.author.id}, {currency[2]}, {money}, {(10 - rating) / 100},"
                    f" {int(time.time())}, {int(time.time()) + (days * 86400)}, 'C', {guarantor})")
                conn.commit()
                cur.execute(f'UPDATE users SET currency_{currency[2]} = currency_{currency[2]} + {money}'
                            f' WHERE uid = {inter.author.id} AND system = {system}')
                conn.commit()
                await inter.response.send_message(
                    embed=disnake.Embed(title='Банк', description=f'Вам выдан кредит на сумму {money}.'))
                return
            await inter.response.send_message(
                embed=disnake.Embed(
                    title='Банк', description='Мы не можем выдать вам кредит на столь длительный срок.'))
            return
        await inter.response.send_message(
            embed=disnake.Embed(
                title='Банк',
                description=f'Мы не можем выдать вам кредит на сумму, большую {10 ** (2 + rating) * currency[1]}.'))

    @commands.slash_command()
    async def repay(self, inter, repayment: int):  # Возврат кредита
        system = get_system(inter.guild.id)
        cur.execute(f"SELECT value, currency FROM bank"
                    f" WHERE uid = {inter.author.id} AND system = {system} AND type = 'C'")
        if repayment <= 0:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У нас серьёзное заведение, а не цирк.'))
            return
        credit = cur.fetchone()
        if not credit:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У вас нет кредитов в нашем банке.'))
            return
        money, currency = credit
        cur.execute(f"SELECT currency_{currency} FROM users WHERE uid = {inter.author.id} AND system = {system}")
        cash = cur.fetchone()[0]
        if cash < repayment:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У вас недостаточно средств.'))
        elif repayment > money:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title='Банк', description='Мы благодарны за вашу доброту, но у нас честный бизнес.'))
        elif repayment == money:
            cur.execute(f'SELECT reg_time FROM bank WHERE uid = {inter.author.id} AND system = {system}')
            if cur.fetchone()[0] // 86400 < time.time() // 86400:
                cur.execute(f'UPDATE users SET social_rating = social_rating + 1 WHERE uid = {inter.author.id}')
            cur.execute(f'DELETE FROM bank WHERE uid = {inter.author.id} AND system = {system}')
            cur.execute(f'UPDATE users SET currency_{currency} = currency_{currency} - {repayment} '
                        f'WHERE uid = {inter.author.id} AND system = {system}')
            conn.commit()
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='Вы успешно выплатили кредит'))
        else:
            cur.execute(f'UPDATE users SET currency_{currency} = currency_{currency} - {repayment} '
                        f'WHERE uid = {inter.author.id}')
            cur.execute(f'UPDATE bank SET currency_{currency} = currency_{currency} - {repayment} '
                        f'WHERE uid = {inter.author.id}')
            conn.commit()
            cur.execute(f'SELECT emoji FROM currencies WHERE id = {currency} AND system = {system}')
            await inter.response.send_message(
                embed=disnake.Embed(
                    title='Банк', description=f'Вы вернули {repayment}{cur.fetchone()[0]} от кредита.'
                                              f' Осталось выплатить {money - repayment}.'))

    @commands.slash_command()
    async def get_deposit(self, inter, money: int, days: int, currency: str = None):
        cur.execute(f"SELECT * FROM bank WHERE uid = {inter.author.id}")
        if money <= 0:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У нас серьёзное заведение, а не цирк.'))
            return
        elif cur.fetchone() is not None:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк',
                                    description='Вы не можете выполнять несколько операций '
                                                'в нашем банке одновременно.'))
            return
        system = get_system(inter.guild.id)
        currency = get_currency(currency, system)
        cur.execute(f"SELECT is_crypt, great_unit, id, emoji, name FROM currencies "
                    f"WHERE name = '{currency}' and system = {system}")
        currency = cur.fetchone()
        if not currency:
            await inter.response.send_message('Название валюты указано неверно')
            return
        if currency[0]:
            await inter.response.send_message('Мы не выдаём кредиты в криптовалюте')
            return
        cur.execute(f'SELECT social_rating, guarantor FROM users '
                    f'WHERE uid = {inter.author.id} AND system = {system}')
        rating, guarantor = cur.fetchone()
        if guarantor:
            cur.execute(f'SELECT social_rating FROM users WHERE uid = {guarantor}')
            guarantor_rating = cur.fetchone()[0]
        else:
            guarantor_rating = 0
        rating = (rating + 3) // 4
        if rating > 5:
            rating = 5
        if guarantor_rating > 5:
            guarantor_rating = 5
        if money <= 10 ** (2 + max(rating, guarantor_rating)) * currency[1]:
            if days < 29:
                cur.execute(
                    f"INSERT INTO bank(system, uid, currency, value, rate, reg_time, end_time, type) VALUES "
                    f"({system}, {inter.author.id}, {currency[2]}, {money}, {(10 - rating) / 100},"
                    f" {int(time.time())}, {int(time.time()) + (days * 86400)}, 'D')")
                conn.commit()
                cur.execute(f'UPDATE users SET currency_{currency[2]} = currency_{currency[2]} - {money}'
                            f' WHERE uid = {inter.author.id} AND system = {system}')
                conn.commit()
                await inter.response.send_message(
                    embed=disnake.Embed(title='Банк', description=f'Вы сделали вклад на сумму {money}.'))
                return
            await inter.response.send_message(
                embed=disnake.Embed(
                    title='Банк', description='Вы не можте сделать вклад на столь длительный срок.'))
            return
        await inter.response.send_message(
            embed=disnake.Embed(
                title='Банк',
                description=f'Вы не можте сделать вклад на сумму, большую {10 ** (2 + rating) * currency[1]}.'))

    @commands.slash_command()
    async def bank_help(self, inter):
        await inter.response.send_message(embed=disnake.Embed(title='Банк', description=bank))

    @commands.slash_command()
    async def guarantee(self, inter, client: disnake.Member):
        system = get_system(inter.guild.id)
        cur.execute(f'SELECT guarantor FROM users WHERE uid = {client.id} AND system = {system}')
        if not cur.fetchone()[0]:
            cur.execute(f'UPDATE users SET guarantor = {inter.author.id} WHERE uid = {client.id} and system = {system}')
            conn.commit()
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description=f'Вы поручились за {client}.'))
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description='У этого пользователя уже есть поручитель.'))

    @commands.slash_command()
    async def guarantee_off(self, inter, client: disnake.Member):
        system = get_system(inter.guild.id)
        cur.execute(f'SELECT guarantor FROM users WHERE uid = {client.id} AND system = {system}')
        if cur.fetchone()[0] == inter.author.id:
            cur.execute(f'UPDATE users SET guarantor = NULL WHERE uid = {client.id} AND system = {system}')
            conn.commit()
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description=f'Вы больше не являетесь поручителем {client}.'))
        else:
            await inter.response.send_message(
                embed=disnake.Embed(title='Банк', description=f'Вы не являетесь поручителем {client}.'))


def setup(bot):
    bot.add_cog(Bank(bot))
