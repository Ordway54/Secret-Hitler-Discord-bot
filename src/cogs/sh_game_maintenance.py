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
        self.guild = self.bot.guilds[0]
        # self.category = discord.utils.get(self.guild.categories, name="Secret Hitler")

    @commands.command()
    @commands.is_owner()
    async def r(self, context: Context):
        """Reloads the commands"""

        await self.bot.reload_extension('cogs.sh_game_maintenance')
        print('Done reloading!')

    @commands.command(aliases=('sh','startsh','shstart'))
    async def create_game(self, context: Context):
        """Creates a new game and corresponding text channel."""

        print('creating a game')
        
        admin_id = context.message.author.id
        
        # check if player is host of another active game
        for game in self.active_games.values():
            game: Game
            if game.admin_id == admin_id:
                await context.channel.send(f"<@{admin_id}>, you are the host of a game that's already in progress. Please issue the `.delete_game` command before creating a new one.")
                return
        
        guild = context.channel.guild
        game_id = str(len(self.active_games) + 1)
        game = Game(game_id, admin_id)
        self.active_games[game_id] = game

        # create channel category and text channel for game instance
        category_name = f"Secret Hitler Game {game.get_id()}"
        channel_name = f"SH main"

        if not self.category_exists(guild, category_name):
            game.category = await guild.create_category(name=category_name)
            game.text_channel = await guild.create_text_channel(channel_name,category=game.category)

        # await game.text_channel.send("Welcome to Secret Hitler!\nRules: https://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
        self.create_lobby_embed(game)
        await game.text_channel.send(embed=game.lobby_embed)
        await context.channel.send("Game channels have been created.")
    

    @commands.command()
    async def delete_game(self, context: Context):
        """Deletes a game and the corresponding text channel."""
        
        print('delete a game')
        author_id = context.message.author.id

        # loop through active games to see which one to delete
        for game in self.active_games.values():
            game: Game

            # admins can only delete the game they started
            if game.admin_id == author_id:
                txt_channel = discord.utils.get(self.category.text_channels, name=f'sh_{game.game_id}')
                if txt_channel is None:
                    print("something went wrong and couldn't find the channel")
                    return
                
                # delete the text channel and clear the active game
                txt_channel: discord.TextChannel
                await txt_channel.delete()
                self.active_games.pop(game.game_id)
                del game

                # This was the last active game, delete the category 
                if len(self.active_games) == 0:
                    await self.category.delete()
                    self.category = None
                return

        # user wasn't an admin of any game, so they can't delete anything
        await context.channel.send(f'<@{author_id}>, you are not the host of any active games.')
        
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
        game.lobby_embed.add_field(name=f"# of Players Required:",value=f"{Game.MIN_PLAYERS}-{Game.MAX_PLAYERS}")
        game.lobby_embed.add_field(name="Players:",value="\n".join([player.name for player in game.players]))



async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))