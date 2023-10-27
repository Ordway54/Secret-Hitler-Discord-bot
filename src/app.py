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

def get_game_with_player(player_id):
    """Returns Game reference if player_id matches a player in a Game."""

    for _,game in active_games.items():
        game: Game
        if game.has_player(player_id):
            return game
    return None


async def send_player_roles(game: Game):
    """Sends all players in the Game their secret role via DM."""
    
    for player in game.players:
        player: Player

        user = bot.get_user(player.get_id())

        if user is not None:
            msg = await user.send(content=f"Your role: {player.role}\nYour party membership: {player.get_party()}",delete_after=8)



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.load_extension('cogs.sh_game_maintenance')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):

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
            

@bot.event
async def on_button_click(interaction: discord.Interaction):
    print('this was triggered', type(interaction))


token = os.environ.get('BOT_TOKEN')
if token is None:
    print("Could not get Bot Token!")
    exit(0)

bot.run(token)