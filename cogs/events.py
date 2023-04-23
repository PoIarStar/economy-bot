from main import cur, conn
from disnake.ext import commands, tasks
from time import time
from datas import great_unit_cnt

import disnake


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stock_market.start()
        self.update_bank.start()

    @commands.Cog.listener()
    async def on_ready(self):
        cur.execute("SELECT guild, system FROM guilds WHERE system IS NOT NULL")
        for i in cur.fetchall():
            for j in self.bot.get_guild(i[0]).members:
                cur.execute("SELECT uid, system FROM users")
                n = cur.fetchall()
                if (j.id, i[1]) not in n:
                    cur.execute(f"INSERT INTO users(uid, system) VALUES ({j.id}, {i[1]})")
                    conn.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {member.guild.id}")
        system = cur.fetchone()[0]
        cur.execute(f"SELECT * FROM users WHERE uid = {member.id} AND system = {system}")
        if not cur.fetchone():
            cur.execute(f"INSERT INTO users(uid, system) VALUES ({member.id}, {system})")
            conn.commit()

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter, error):
        if isinstance(error, commands.CommandOnCooldown):
            await inter.response.send_message(f'У нас перерыв. Приходите <t:{int(error.retry_after + time())}:R>')

    @tasks.loop(hours=1)
    async def update_stock_market(self):
        cur.execute('SELECT id, system FROM currencies')
        for i in cur.fetchall():
            cur.execute(f'SELECT currency_{i[0]} FROM users WHERE system = {i[1]}')
            money = cur.fetchall()
            cur.execute(
                f'UPDATE currencies SET great_unit = {sum((i[0] for i in money)) / len(money) * great_unit_cnt}')
            conn.commit()

    @tasks.loop(hours=1)
    async def update_bank(self):
        if time() % 86400 < 3600:
            cur.execute('UPDATE bank SET value = value + value * rate')
        cur.execute(f"UPDATE bank SET value = value * 2 WHERE end_time < {time()} AND type = 'C' AND rate <> 0")
        cur.execute(f'SELECT system, uid, type, currency, value, guarantor FROM bank WHERE end_time < {time()}')
        for i in cur.fetchall():
            if i[2] == 'C':
                cur.execute(f"UPDATE bank SET rate = 0 WHERE end_time < {time()} AND type = 'C'")
                for j in self.bot.guilds:
                    cur.execute(f'SELECT alert_channel FRMO guilds WHERE guild = {j.id}')
                    channel = cur.fetchone()
                    cur.execute(f'SELECT system FROM guilds WHERE guild = {j.id}')
                    if cur.fetchone()[0] == i[0] and j.get_member(i[1]) and channel:
                        await j.get_channel(channel).send(
                            embed=disnake.Embed(
                                description=f'<@{i[1]}>, срок кредита истёк истёк. Начисление процентов прекращено.'
                                            f' К оплате {i[4]}'))
                        break
            else:
                cur.execute(f'UPDATE users SET currency_{i[3]} = currency_{i[3]} + {i[4]} WHERE uid = {i[1]} '
                            f'AND system = {i[0]}')
                cur.execute(f'DELETE FROM bank WHERE uid = {i[1]} AND system = {i[0]}')
                for j in self.bot.guilds:
                    cur.execute(f'SELECT alert_channel FRMO guilds WHERE guild = {j.id}')
                    channel = cur.fetchone()
                    cur.execute(f'SELECT system FROM guilds WHERE guild = {j.id}')
                    if cur.fetchone()[0] == i[0] and j.get_member(i[1]) and channel:
                        await j.get_channel(channel).send(
                            embed=disnake.Embed(
                                description=f'<@{i[1]}>, срок вклада истёк. Средства возвращены на основной счёт'))
                        break

    @commands.Cog.listener()
    async def on_message(self, message):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {message.guild.id}")
        system = cur.fetchone()[0]
        cur.execute(f"SELECT flood_channel FROM guilds WHERE guild = {message.guild.id}")
        n = cur.fetchone()
        try:
            n = n if n[0] else ((0,),)
        except Exception as e:
            print(e)
        if not message.author.bot and message.channel.id not in n[0]:
            cur.execute(f"UPDATE users SET xp = xp + {len(message.content) // 75 + 1} WHERE uid "
                        f"= {message.author.id} AND system = {system}")
            conn.commit()
            cur.execute(f"SELECT xp, lvl FROM users WHERE uid = {message.author.id} "
                        f"AND system = {system}")
            xp, lvl = cur.fetchone()
            while xp >= lvl * 25:
                xp -= lvl * 25
                lvl += 1
            cur.execute(f"UPDATE users SET lvl = {lvl}, xp = {xp} WHERE uid = {message.author.id} "
                        f"AND system = {system}")
            conn.commit()
        await self.mirror_ball()

    async def mirror_ball(self):
        for i in self.bot.guilds:
            cur.execute(f"SELECT color_role FROM guilds WHERE guild = {i.id}")
            role = cur.fetchone()
            if role:
                if role[0]:
                    role = i.get_role(role[0])
                    color = [i // 5 * 5 for i in list(role.color.to_rgb())]
                    bright = min(color)
                    color = [i - bright for i in color]
                    if not color[2] and not color[1]:
                        if color[0] < 255 - bright:
                            color[0] += 5
                        else:
                            color[1] += 5
                    elif not color[2] and not color[0]:
                        if color[1] < 255 - bright:
                            color[1] += 5
                        else:
                            color[2] += 5
                    elif not color[0] and not color[1]:
                        if color[2] < 255 - bright:
                            color[2] += 5
                        else:
                            color[0] += 5
                    elif not color[0]:
                        if color[1] > color[2]:
                            color[2] += 5
                        else:
                            color[1] -= 5
                    elif not color[1]:
                        if color[2] > color[0]:
                            color[0] += 5
                        else:
                            color[2] -= 5
                    elif not color[2]:
                        if color[0] > color[1]:
                            color[1] += 5
                        else:
                            color[0] -= 5

                    color = [i + bright for i in color]
                    colour = disnake.Color.from_rgb(*color)
                    await role.edit(color=colour)


def setup(bot):
    bot.add_cog(Events(bot))
