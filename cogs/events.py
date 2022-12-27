from main import cur, conn
from disnake.ext import commands
import disnake


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
        try:
            n = n if n[0] else ((0,),)
        except:
            pass
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
        await self.mirror_ball()

    async def mirror_ball(self):
        for i in self.bot.guilds:
            cur.execute(f"SELECT color_role FROM guilds WHERE guild = {i.id}")
            role = cur.fetchone()
            if role:
                if role[0]:
                    r = role[0]
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
