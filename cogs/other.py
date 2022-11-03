import disnake
from disnake.ext import commands
import random
from main import cur
# import aiohttp


class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.slash_command()
    # async def suggest(self, inter, text):
    #    suggest_hook = disnake.Webhook.from_url('https://discord.com/api/webhooks/983728997642944562/28fIZHMCxnhRPS'
    #                                            'OoQ6N6V5G7n0e_2XxoeCfTYLp9dzvrsSceMspTm1bcODeS0ISH4D2U',
    #                                            session=aiohttp.ClientSession())
    #    emb = disnake.Embed(title='Предложение', description=text.capitalize())
    #    await suggest_hook.send(username=inter.author.name, embed=emb, avatar_url=inter.author.avatar.url)
    #    await aiohttp.ClientSession.close()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Other succesfully loaded")

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def add_flood_channel(self, inter, channel: disnake.TextChannel):
        cur.execute(f"SELECT flood_channel FROM guilds WHERE guild = {inter.guild.id}")
        n = cur.fetchone()[0]
        print(n)
        if channel.id in n:
            await inter.response.send_message('Этот канал уже является каналом для флуда')
        else:
            cur.execute(f"UPDATE guilds SET flood_channel = array_append(flood_channel, {channel.id}) WHERE "
                        f"guild = {inter.guild.id}")
            await inter.response.send_message('Успешно')

    @commands.slash_command()
    async def random_user(self, inter):
        await inter.response.send_message(random.choice(inter.guild.members))

    @commands.slash_command()
    async def roll(self, inter, first: int = 0, second: int = 100, step: int = 1):
        await inter.response.send_message(random.randrange(first, second, step))

    @commands.slash_command(name='8ball')
    async def ball(self, inter, event):
        n = random.choice(
            ['бесспорно', 'предрешено', 'никаких сомнений', 'определённо, да', 'можешь быть уверен в этом',
             'мне кажется, да', 'вероятнее всего', 'хорошие перспективы', 'знаки говорят "да"', 'да',
             'пока не ясно, попробуй снова', 'спроси позже', 'лучше не рассказывать', 'сейчас нельзя предсказать',
             'сконцентрируйся и спроси опять', 'даже не думай', 'мой ответ — "нет"', 'по моим данным, нет',
             'перспективы не очень хорошие', 'весьма сомнительно'])
        await inter.response.send_message(f'Что касается события "{event}", {n}')

    @commands.slash_command()
    async def write(self, inter, text: str, channel: disnake.TextChannel):
        await channel.send(text)

    @commands.slash_command()
    async def reply_message(self, inter, text: str, channel: disnake.TextChannel, message):
        await channel.get_partial_message(int(message)).reply(text)


def setup(bot):
    bot.add_cog(Other(bot))
