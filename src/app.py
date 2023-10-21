# Discord bot
from game import Game, GameState
import discord
from discord.ext import commands

intents = discord.Intents.all()
intents.message_content = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='.',intents=intents)

active_games = {}

def get_game_with_player(player_id):
    """Returns Game reference if player_id matches a player in a Game."""

    for _,game in active_games.items():
        game: Game
        if game.has_player(player_id):
            return game
    return None
        

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await bot.process_commands(message.channel.send('Hello!'))
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    print('reaction dude!')
    if user.id == bot.user.id:
        # ignore reactions made by bot
        return
    
    # get reference to Game instance associated with user
    game = get_game_with_player(user.id)

    if game is None:
        # user is not in an active game, remove their reaction
        reaction: discord.Reaction
        await reaction.remove(user)
        return
    
    if game.state == GameState.ELECTION:
        vote = None

        if "ja" in reaction.emoji.name.lower():
            vote = game.vote(user.id, 'yes')
        elif "nein" in reaction.emoji.name.lower():
            vote = game.vote(user.id, 'no')

        if vote is None:
            # user reacted with unrelated emoji. ignore.
            await reaction.remove(user)
            return
        
        if len(game.votes) == len(game.players):
            # all players have voted, end voting sequence
            game.tally_votes()
            

@bot.command(name='start')
async def start_game(context):
    print('starting game')
    admin_id = context.message.author.id
    channel_id = context.message.channel.id
    game_id = "game_" + str(len(active_games) + 1)
    max_players = 10 # hard coded for now

    game = Game(channel_id,game_id,admin_id,max_players)

    active_games[game_id] = game


@bot.command(aliases=("terms","legal","license"))
async def send_licensing(context):
    print('legal')
    title = "Credits & License"
    description = Game.game_license_terms
    url = "https://www.secrethitler.com/"
    orange = discord.Color.from_rgb(242,100,74) # "SH orange"
    
    terms_embed = discord.Embed(title=title,description=description,url=url,color=orange)

    await context.channel.send(embed=terms_embed)



bot.run('NzU4NjkwNDA0MTEwOTU4NjUy.GXeYEl.9UMtO9G5ybHkBhKJ93o2PskWud4ES1jStTDItk')