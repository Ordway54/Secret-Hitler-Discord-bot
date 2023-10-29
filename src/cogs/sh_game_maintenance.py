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

        # create channel category and text channel for game instance
        category_name = f"Secret Hitler Game {game.get_id()}"
        channel_name = f"SH main"

        if not self.category_exists(guild, category_name):
            game.category = await guild.create_category(name=category_name)
            game.text_channel = await guild.create_text_channel(channel_name,category=game.category)

        # await game.text_channel.send("Welcome to Secret Hitler!\nRules: https://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
        lobby_embed = self.create_lobby_embed(game)

        game.lobby_embed_msg = await game.text_channel.send(embed=lobby_embed,view=GameLobbyView(game))
        await context.channel.send("Game channels have been created.")

        # the following line is for testing purposes only
        await context.channel.send("Test", view=PresidentialPowerView(game,1))
    

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
                # commented out for testing only
                # await context.author.send(f"Your active SH game has been deleted. You can now create a new one if you wish.", delete_after=30)
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
        pass
    

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
        """Returns a Game Lobby Embed object.
        
        Params:
        game: a Game object
        
        Returns:
        discord.Embed"""

        title = f"Secret Hitler Game Lobby (Game {game.get_id()})"

        lobby_embed = discord.Embed(title=title,color=Game.SH_ORANGE)
        lobby_embed.add_field(name=f"# of Players Required:",
                                   value=f"{Game.MIN_PLAYERS}-{Game.MAX_PLAYERS}",
                                   inline=False)
        lobby_embed.add_field(name="Players:",value="\n".join([player.name for player in game.players]))

        return lobby_embed


class GameLobbyView(discord.ui.View):
    """Represents a Game Lobby View."""
    
    def __init__(self, game: Game):
        super().__init__()
        self.game = game

    
    @discord.ui.button(label="Join Lobby", style=discord.ButtonStyle.green)
    async def join_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.message.reply("You joined the game lobby.")
        self.game.add_player(interaction.user.id, interaction.user.name)
        embed = self.game.lobby_embed_msg.embeds[0]
        embed.set_field_at(1,name="Players in Lobby",value="\n".join([player.name for player in self.game.players]))
        await self.game.lobby_embed_msg.edit(embed=embed)
    
        
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.red)
    async def leave_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.message.reply("You left the game lobby.")
        self.game.remove_player(interaction.user.id)
        embed = self.game.lobby_embed_msg.embeds[0]
        embed.set_field_at(1,name="Players in Lobby",value='\n'.join([player.name for player in self.game.players]))
        await self.game.lobby_embed_msg.edit(embed=embed)
    
    @discord.ui.button(label="Abandon Lobby",style=discord.ButtonStyle.red)
    async def abandon_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class PresidentialPowerView(discord.ui.View):
    """Represents the View applied when a Presidential Power is being exercised."""
    
    POWERS = {
        1 : "Investigate Loyalty",
        2 : "Call Special Election",
        3 : "Policy Peek",
        4 : "Execution"}

    def __init__(self, game: Game, pres_power: int):
        """Instantiates the View.
        
        Params:
        game: an instance of the Game class
        pres_power: an int representing the type of Presidential Power being used."""
        super().__init__()
        self.game = game
        self.pres_power = PresidentialPowerView.POWERS.get(pres_power,None)
        self.create_buttons()
    
    def create_buttons(self):

        if self.pres_power == "Investigate Loyalty":
            player_names = self.game.get_investigatable_player_names()

            for name, id in player_names:
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(id),
                                        label=name)
                btn.callback = self.cb_investigate_loyalty
                self.add_item(btn)


        elif self.pres_power == "Call Special Election":
            pass
        elif self.pres_power == "Policy Peek":
            pass
        elif self.pres_power == "Execution":
            pass
        else:
            return False


    async def cb_investigate_loyalty(self,interaction: discord.Interaction):
        """A callback function for the Investigate Loyalty buttons."""
        
        user_is_president = interaction.user.id == self.game.incumbent_president.get_id()
        
        if user_is_president:
            # the custom_id attribute of the button == the id of the player named on its label
            player_id = int(interaction.data.get('custom_id'))
            player_to_investigate = self.game.get_player(player_id)

            msg = (
                f"""
                You chose to investigate {player_to_investigate.name}.
                They are a member of the {player_to_investigate.get_party()} party.\n
                **Remember:** You may choose to share this information (or 
                lie about it!) with other players, but you may **not** show 
                this message as proof in any way, shape, or form, to any other player.
                """)
            
            await interaction.user.send(msg, delete_after=15)
            await interaction.message.channel.send(
                f"""President {interaction.user.name} chose to investigate the party loyalty of {player_to_investigate.name}!""")



async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))

