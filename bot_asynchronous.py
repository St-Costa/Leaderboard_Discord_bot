import os
import io
import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
import aiohttp

# Carica il token dal file .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Imposta tutti gli intents necessari (versione aggiornata)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True   # Fondamentale per bot classici

bot = commands.Bot(command_prefix="!", intents=intents)

TEST_CHANNEL_ID = 1396023104366706719

@bot.event
async def on_ready():
    print(f"Bot online come {bot.user}")
    channel = bot.get_channel(TEST_CHANNEL_ID)
    if channel:
        await post_leaderboard(channel, channel.guild)


async def send_role_embed(channel, members, title, color):
    avatars = []
    async with aiohttp.ClientSession() as session:
        for m in members:
            url = m.avatar.url if m.avatar else m.default_avatar.url
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    avatar_img = Image.open(io.BytesIO(data)).resize((64, 64))
                    avatars.append(avatar_img)

    cols = min(8, len(avatars))
    rows = (len(avatars) + cols - 1) // cols
    collage = Image.new('RGBA', (cols * 64, rows * 64), (255, 255, 255, 0))
    for idx, avatar in enumerate(avatars):
        x = (idx % cols) * 64
        y = (idx // cols) * 64
        collage.paste(avatar, (x, y))

    with io.BytesIO() as image_binary:
        collage.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="collage.png")
        member_list = ", ".join([m.mention for m in members])
        embed = discord.Embed(title=title, description=member_list, color=color)
        embed.set_image(url="attachment://collage.png")
        await channel.send(embed=embed, file=file)


async def post_leaderboard(channel, guild):
    # Leaderboard banner
    embed = discord.Embed()
    with open("./banner_leaderboard.jpg", "rb") as f:
        file = discord.File(f, filename="leaderboard_banner.png")
        embed.set_image(url="attachment://leaderboard_banner.png")
        await channel.send(embed=embed, file=file)

    # Exclude @everyone, "L'aggiustatutto", and "Ex membro" from the leaderboard
    roles = [
        role for role in guild.roles
        if role != guild.default_role
        and role.members
        and role.name != "L'aggiustatutto"
        and role.name != "Ex membro"
    ]
    roles = sorted(roles, key=lambda r: r.position, reverse=False)

    for role in roles:
        members = [m for m in role.members if not m.bot]
        if not members:
            continue
        await send_role_embed(channel, members, role.name, role.color)



@bot.command()
async def leaderboard(ctx):
    await post_leaderboard(ctx.channel, ctx.guild)

bot.run(TOKEN)