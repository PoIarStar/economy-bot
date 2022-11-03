from main import cur, conn
from random import randrange
import disnake
from disnake.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.bot.guilds)
        cur.execute("SELECT guild, system FROM guilds WHERE system IS NOT NULL")
        for i in cur.fetchall():
            for j in self.bot.get_guild(i[0]).members:
                cur.execute("SELECT uid, system FROM users")
                n = cur.fetchall()
                if (j.id, i[1]) not in n:
                    cur.execute(f"INSERT INTO users(uid, system) VALUES ({j.id}, {i[1]})")
                    conn.commit()
        print('Events successfully loaded')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {member.guild}")
        system = cur.fetchone()[0]
        cur.execute(f"SELECT * FROM users WHERE uid = {member.id} AND system = {system}")
        if not cur.fetchone():
            cur.execute(f"INSERT INTO users(uid, system) VALUES ({member.id}, {system})")
            conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {message.guild.id}")
        system = cur.fetchone()[0]
        cur.execute(f"SELECT flood_channel FROM guilds WHERE guild = {message.guild.id}")
        n = cur.fetchone()
        n = n if n else ((0,),)
        if not message.author.bot and message.channel.id not in n[0]:
            cur.execute(f"UPDATE users SET xp = xp + {len(message.content) // 75 + 1} WHERE uid "
                        f"= {message.author.id} AND system = {system}")
            conn.commit()
            cur.execute(f"SELECT xp, lvl FROM users WHERE uid = {message.author.id} "
                        f"AND system = {system}")
            xp, lvl = cur.fetchone()
            while xp >= lvl * 25:
                xp = xp - lvl * 25
                lvl = lvl + 1
            cur.execute(f"UPDATE users SET lvl = {lvl}, xp = {xp} WHERE uid = {message.author.id} "
                        f"AND system = {system}")
            conn.commit()
            cur.execute(f"SELECT color_role FROM guilds WHERE guild = {message.guild.id}")
            role = cur.fetchone()
            if role:
                if role[0]:
                    role = message.guild.get_role(role[0])
                    await role.edit(color=randrange(1, 16777215, 10))


def setup(bot):
    bot.add_cog(Events(bot))
