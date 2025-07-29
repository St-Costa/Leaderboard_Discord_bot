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

# Intents necessari
intents = discord.Intents.default()
intents.members = True
intents.message_content = True   

#CHANNEL_ID = 1383125540126326814 # "stato-del-laboratorio"
CHANNEL_ID = 1396023104366706719 # testing_stefano


bot = commands.Bot(command_prefix="!", intents=intents)

async def send_leaderboard(channel, guild):
    # Banner leaderboard
    embed = discord.Embed()
    with open("./banner_leaderboard.jpg", "rb") as f:
        file = discord.File(f, filename="leaderboard_banner.png")
        embed.set_image(url="attachment://leaderboard_banner.png")
        await channel.send(embed=embed, file=file)

    # Exclude @everyone, "L'aggiustatutto", and bot roles
    roles = [
        role for role in guild.roles
        if role != guild.default_role
        and role.members
        and role.name != "L'aggiustatutto"
    ]
    roles = sorted(roles, key=lambda r: r.position, reverse=False)

    # Per ogni ruolo, crea un collage di avatar
    for role in roles:
        members = [m for m in role.members if not m.bot]
        if not members:
            continue

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
            embed = discord.Embed(
                title=role.name,
                description=member_list,
                color=role.color
            )
            embed.set_image(url="attachment://collage.png")
            await channel.send(embed=embed, file=file)

@bot.event
async def on_ready():
    print(f"Bot online come {bot.user}")
    guild = bot.guilds[0]
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Canale non trovato: {CHANNEL_ID}")
    else:
        await channel.purge()                   # Cancella messaggi del canale
        await send_leaderboard(channel, guild)  # Stampa leaderboard
    await bot.close()

bot.run(TOKEN)
