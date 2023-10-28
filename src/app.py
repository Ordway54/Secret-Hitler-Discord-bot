# Discord bot
from game import Game, GameState, Player
import discord
import os
from discord.ext import commands
from discord.ext.commands import Context

intents = discord.Intents.all()
intents.message_content = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='.',intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.load_extension('cogs.sh_game_maintenance')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

token = os.environ.get('BOT_TOKEN')
if token is None:
    print("Could not get Bot Token!")
    exit(0)

bot.run(token)