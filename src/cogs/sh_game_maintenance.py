import discord
from discord.ext import commands
from discord.ext.commands import Context
import sys
sys.path.append('src')
from game import Game

class SHGameMaintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command()
    @commands.is_owner()
    async def r(self, context: Context):
        """Reloads the commands"""

        await self.bot.reload_extension('cogs.sh_game_maintenance')
        print('Done reloading!')

    @commands.command(aliases=('sh','startsh','shstart'))
    async def create_game(self, context: Context):
        """Creates a new game and corresponding text channel."""
        # tested and working as of 10/26/23
        print('creating a game')
        admin_id = context.message.author.id
        
        # check if player is host of another active game
        for game in self.active_games.values():
            game: Game
            if game.admin_id == admin_id:
                await context.channel.send(f"<@{admin_id}>, you are the host of a game that's already in progress. Please issue the `.delgame` command before creating a new one.")
                return
        
        guild = context.channel.guild
        game_id = str(len(self.active_games) + 1)
        game = Game(game_id, admin_id)
        self.active_games[game_id] = game
        print(self.active_games)

        # create channel category and text channel for game instance
        category_name = f"Secret Hitler Game {game.get_id()}"
        channel_name = f"SH main"

        if not self.category_exists(guild, category_name):
            game.category = await guild.create_category(name=category_name)
            game.text_channel = await guild.create_text_channel(channel_name,category=game.category)

        # await game.text_channel.send("Welcome to Secret Hitler!\nRules: https://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
        self.create_lobby_embed(game)
        embed = game.lobby_embed_msg.embeds[0]
        await game.text_channel.send(embed=embed, view=GameLobbyView(game))
        await context.channel.send("Game channels have been created.")
    

    @commands.command(name="delgame")
    async def delete_game(self, context: Context):
        """Deletes a game and the server modifications associated with it."""
        # tested and working as of 10/26/23
        author_id = context.message.author.id

        for game in self.active_games.values():
            game: Game

            if game.admin_id == author_id:
                
                if game.text_channel is not None:
                    await game.text_channel.delete(reason="Secret Hitler game over")
                elif game.text_channel is None:
                    print("Something went wrong. No text channel found.")
                    return
                
                if game.category is not None:
                    await game.category.delete(reason="Secret Hitler game over")
                elif game.category is None:
                    print("Something went wrong. No category found.")
                    return
                
                self.active_games.pop(game.game_id)
                print(self.active_games)
                return

        await context.channel.send(f'<@{author_id}>, you are not the host of any active games.')

    @commands.command(aliases=("terms","legal","license","licensing","tos"))
    async def send_licensing(self, context: Context):
        title = "Credits & License"
        url = "https://www.secrethitler.com/"
        color = Game.SH_ORANGE
        
        terms_embed = discord.Embed(title=title,description=Game.LICENSE_TERMS,url=url,color=color)

        await context.channel.send(embed=terms_embed)

    async def edit_embed_player_list(self):
        self.game.lo

    def text_channel_exists(self, guild: discord.Guild, name: str) -> bool:
        """Check if game text channel exists. If so, return True,\
            otherwise False."""
        
        for channel in guild.channels:
            if channel.name == name:
                return True
        return False

    def category_exists(self, guild: discord.Guild, name: str) -> bool:
        """Check if channel category exists. If so, return True,\
            otherwise False."""
        
        for category in guild.categories:
            if category.name == name:
                return True
        return False
    
    def create_lobby_embed(self, game: Game):
        title = f"Secret Hitler Game Lobby (Game {game.get_id()})"

        game.lobby_embed = discord.Embed(title=title,color=Game.SH_ORANGE)
        game.lobby_embed.add_field(name=f"# of Players Required:",
                                   value=f"{Game.MIN_PLAYERS}-{Game.MAX_PLAYERS}",
                                   inline=False)
        game.lobby_embed.add_field(name="Players:",value="\n".join([player.name for player in game.players]))


class GameLobbyView(discord.ui.View):
    """Represents a Game Lobby embed View."""
    
    def __init__(self, game: Game):
        super().__init__()
        self.game = game

    

    @discord.ui.button(label="Join Lobby", style=discord.ButtonStyle.green)
    async def join_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.lobby_embed is not None:

            self.game.lobby_embed.set_field_at(1,name="Toast is good.",value="\n".join([str(player.name) for player in self.game.players]))
            # self.embed.add_field(name="Players in Lobby:",value="\n".join(self.players))
            await self.game.lobby_embed.edit(embed=self.game.lobby_embed)
    
        
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.red)
    async def leave_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.embed_message is not None:
            if interaction.user.name in self.players:
                self.players.remove(interaction.user.name)
                self.embed.clear_fields()
                self.embed.add_field(name="Players in Lobby:",value="\n".join(self.players))
                await self.embed_message.edit(embed=self.embed)



async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))

