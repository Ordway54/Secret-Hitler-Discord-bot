# Discord bot
from game import Game, GameState
import discord

# This example requires the 'message_content' intent.

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

active_games = {}

def get_game_with_player(player_id):
    """Returns Game reference if player_id matches a player in a Game."""

    for _,game in active_games.items():
        game: Game
        if game.has_player(player_id):
            return game
    return None
        

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

@client.event
async def on_reaction_add(reaction, user):
    if user.id == client.user.id:
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
            

@client.event(name="startSH")
async def start_game(context):
    admin_id = context.message.author.id
    channel_id = context.message.channel.id
    game_id = "game_" + str(len(active_games) + 1)
    max_players = 10 # hard coded for now

    game = Game(channel_id,game_id,admin_id,max_players)

    active_games[game_id] = game



client.run('your token here')