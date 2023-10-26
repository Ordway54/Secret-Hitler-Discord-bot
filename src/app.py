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
        

class GameLobby(discord.ui.View):
    
    def __init__(self, context: Context, game: Game):
        self.embed_message = self.create_lobby_embed(context)
        super().__init__()

        self.game = game
        self.game.add_player(context.message.author.id,context.message.author.name)
        
        
    

    @discord.ui.button(label="Join Lobby", style=discord.ButtonStyle.green)
    async def join_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.embed_message is not None:
            self.embed.set_field_at(1,name="Toast is good.",value="\n".join(self.game.players))
            # self.embed.add_field(name="Players in Lobby:",value="\n".join(self.players))
            await self.embed_message.edit(embed=self.embed)
        else:
            if interaction.user.name not in self.players:
                self.players.append(interaction.user.name)
                self.embed.clear_fields()
                self.embed.add_field(name="Players in Lobby:",value="\n".join(self.players))
            self.embed_message = await interaction.channel.send(embed=self.embed)
    
        
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.red)
    async def leave_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.embed_message is not None:
            if interaction.user.name in self.players:
                self.players.remove(interaction.user.name)
                self.embed.clear_fields()
                self.embed.add_field(name="Players in Lobby:",value="\n".join(self.players))
                await self.embed_message.edit(embed=self.embed)

async def create_lobby_embed(self, context: Context):
    """Creates a Secret Hitler Game Lobby embed."""
    title = f"Secret Hitler - Game {self.game.game_id}"
    self.embed = discord.Embed(title=title,color=Game.SH_ORANGE)
    self.embed.add_field(name="Min/Max Players:",value="5/10", inline=True)
    self.embed.add_field(name="Players in Lobby:",value="\n".join(self.game.players))
    return await context.channel.send(embed=self.embed)

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
            

@bot.command(name='start')
async def start_game(context: Context):

    admin_id = context.message.author.id
    channel_id = context.message.channel.id
    game_id = "game_" + str(len(active_games) + 1)
    max_players = 10 # hard coded for now

    game = Game(channel_id,game_id,admin_id,max_players)

    active_games[game_id] = game


@bot.command(name='s')
async def s(context: Context):
    # this is a test function only
    await context.reply("Starting game of Secret Hitler...")
    
    a = Game(len(active_games)+1,context.author.id)
    view = GameLobby(context,a)
    await context.send("", view=view)
    # await send_player_roles(a)


@bot.event
async def on_button_click(interaction: discord.Interaction):
    print('this was triggered', type(interaction))

@bot.command(aliases=("terms","legal","license"))
async def send_licensing(context: Context):
    title = "Credits & License"
    description = Game.game_license_terms
    url = "https://www.secrethitler.com/"
    color = Game.SH_ORANGE
    
    terms_embed = discord.Embed(title=title,description=description,url=url,color=color)

    await context.channel.send(embed=terms_embed)


token = os.environ.get('BOT_TOKEN')
if token is None:
    print("Could not get Bot Token!")
    exit(0)

bot.run(token)