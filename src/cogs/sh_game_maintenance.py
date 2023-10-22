import discord
from discord.ext import commands
from discord.ext.commands import Context
from src import game

class SHGameMaintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.guild = self.bot.guilds[0]
        self.category = discord.utils.get(self.guild.categories, name="Secret Hitler")

    @commands.command()
    @commands.is_owner()
    async def r(self, context):
        '''
        Reloads the commands
        '''
        await self.bot.reload_extension('cogs.sh_game_maintenance')
        print('Done reloading!')

    @commands.command()
    async def create_game(self, context: Context):
        '''
        Create a new game and corresponding text channel
        '''
        print('create a game')
        admin_id = context.message.author.id
        channel_id = context.message.channel.id
        game_id = "Game_" + str(len(self.active_games) + 1)
        max_players = 10 # hard coded for now

        for game in self.active_games.values():
            game: Game
            if game.admin_id == admin_id:
                await context.channel.send(f"<@{admin_id}>, you are the host of a game that's already in progress. Please issue the `.delete_game` command before creating a new one.")
                return

        game = Game(channel_id, game_id, admin_id, max_players)
        self.active_games[game_id] = game

        # if there is no Secret Hitler category, create one
        if self.category is None:
            self.category = await self.guild.create_category(name=f"Secret Hitler")

        # make sure the text channel does not exist
        if discord.utils.get(self.category.text_channels, name=f'SH_{game_id}') is not None:
            print('The game channel already exists, is that an error...?')
            return
        
        await self.category.create_text_channel(f'SH_{game_id}')

        # now prompt people to join the game using buttons
    
    @commands.command()
    async def delete_game(self, context: Context):
        '''
        Delete a game and the corresponding text channel
        '''
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
        

async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))