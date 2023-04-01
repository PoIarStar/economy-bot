from main import cur, conn
from random import randint
import disnake
from disnake.ext import commands


class Connection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def system_info(self, inter):
        cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
        id = cur.fetchone()[0]
        if id:
            cur.execute(f'SELECT name FROM systems WHERE id = {id}')
            name = f'Ваш сервер подключен к экономической системе "{cur.fetchone()[0]}"'
        else:
            name = 'Ваш сервер не подключен к экономической системе'
        await inter.response.send_message(embed=disnake.Embed(title='Информация', description=name))

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def create_system(self, inter, sys_name, password):
        cur.execute("SELECT id FROM systems")
        ids = cur.fetchall()
        n = randint(0, 99999999)
        while n in ids:
            n = randint(0, 99999999)
        cur.execute(f"INSERT INTO systems(id, name, password) VALUES ({n}, '{sys_name}', '{password}')")
        conn.commit()
        await inter.response.send_message(f'Экономическая система успешно создана. Идентификатор системы - {n}. '
                                          'Идентификатор используется при добавлении серверов к экономической системе. '
                                          'Пожалуйста, сохраните его.', ephemeral=True)
        await inter.author.send(
            f'Вы создали новую экономическую систему. Идентификатор - ||{n}||, пароль - ||{password}||')

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def delete_system(self, inter, id, password):
        cur.execute(f"SELECT id, password FROM systems WHERE id = {id}")
        n = cur.fetchone()
        if not n:
            await inter.response.send_message(f'Данной экономической системы не существует. Вы точно не мошенник?',
                                              ephemeral=True)
        elif n[1] == password:
            cur.execute(f"DELETE FROM systems WHERE id = {id}")
            cur.execute(f'UPDATE guilds SET system = NULL WHERE system = {id}')
            conn.commit()
            await inter.response.send_message(f'Экономическая система удалена', ephemeral=True)
            await inter.channel.send(
                embed=disnake.Embed(
                    title='Подключение',
                    description=f'Ваш сервер отключен от экономической системы'))
        else:
            await inter.response.send_message(f'Неверный пароль', ephemeral=True)

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def connect_system(self, inter, id: int, password):
        cur.execute(f"SELECT id, password FROM systems WHERE id = {id}")
        n = cur.fetchone()
        if not n:
            await inter.response.send_message(f'Данной экономической системы не существует. Вы точно не мошенник?',
                                              ephemeral=True)
        elif n[1] == password:
            cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
            n = cur.fetchone()
            if not n:
                cur.execute(f"INSERT INTO guilds(guild, system) VALUES ({inter.guild.id}, {id})")
                conn.commit()
            elif all(n):
                await inter.response.send_message(f'Этот сервер уже подключен к экономической системе. Если хотите из'
                                                  'менить её, отключите сервер от текущей.',
                                                  ephemeral=True)
                return
            else:
                cur.execute(f"UPDATE guilds SET system = {id} WHERE guild = {inter.guild.id}")
                conn.commit()
            cur.execute("SELECT uid, system FROM users")
            n = cur.fetchall()
            for i in inter.guild.members:
                if (i.id, id) not in n:
                    cur.execute(f"INSERT INTO users(uid, system) VALUES ({i.id}, {id})")
                    conn.commit()
            cur.execute(f"SELECT name FROM systems WHERE id = {id}")
            name = cur.fetchone()[0]
            await inter.response.send_message(f'Успешно', ephemeral=True)
            await inter.channel.send(
                embed=disnake.Embed(
                    title='Подключение',
                    description=f'Ваш сервер подключен к экономической системе "{name}"'))
        else:
            await inter.response.send_message(f'Неверный пароль', ephemeral=True)

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def disconnect_system(self, inter, id, password):
        cur.execute(f"SELECT id, password FROM systems WHERE id = {id}")
        n = cur.fetchone()
        if not n:
            await inter.response.send_message(f'Данной экономической системы не существует. Вы точно не мошенник?',
                                              ephemeral=True)
        elif n[1] == password:
            cur.execute(f"SELECT system FROM guilds WHERE guild = {inter.guild.id}")
            n = cur.fetchone()
            if all(n):
                cur.execute(f"UPDATE guilds SET system = NULL WHERE guild = {inter.guild.id}")
                conn.commit()
                await inter.response.send_message(
                    f'Сервер успешно отключен от экономической системы',
                    ephemeral=True)
                await inter.channel.send(
                    embed=disnake.Embed(
                        title='Подключение',
                        description='Ваш сервер отключен от экономической системы.'))
            else:
                await inter.response.send_message(
                    f'Этот сервер не подключен к экономической системе.',
                    ephemeral=True)


def setup(bot):
    bot.add_cog(Connection(bot))
