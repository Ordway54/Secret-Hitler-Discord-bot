import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
import asyncio
import re
import sys
sys.path.append('src')
from game import Game, GameState

# Testing constants
DEL_AFTER_TIME = 10

class SHGameMaintenance(commands.Cog):

    NO_SHARE_WARNING = ("""
                        **Remember:** You may choose to share this information (or 
                        lie about it!) with other players, but you may **not** show/share 
                        this message as proof in any way, shape, or form, to any other player.
                        """)
    
    INVESTIGATE_LOYALTY = "Investigate Loyalty"
    SPECIAL_ELECTION = "Call Special Election"
    POLICY_PEEK = "Policy Peek"
    EXECUTION = "Execution"


    def __init__(self, bot: Bot):
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

        print('creating a game')
        admin_id = context.message.author.id
        
        # check if player is host of another active game
        for game in self.active_games.values():
            game: Game
            if game.admin_id == admin_id:
                msg = self.strip_spacing(f"""<@{admin_id}>, you are the host\
                    of a game that's already in progress. Please issue the\
                    `.delgame` command before creating a new one.""")
                await context.channel.send(msg)              
                return
        
        guild = context.channel.guild
        game_id = str(len(self.active_games) + 1)
        game = Game(game_id, admin_id)
        self.active_games[game_id] = game

        # create channel category and text channel for game instance
        category_name = f"SH Game {game.get_id()}"
        channel_name = f"main"

        if not self.category_exists(guild, category_name):
            game.category = await guild.create_category(name=category_name)
            game.text_channel = await guild.create_text_channel(channel_name,category=game.category)

        # await game.text_channel.send("Welcome to Secret Hitler!\nRules: https://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
        lobby_embed = self.create_lobby_embed(game)

        game.lobby_embed_msg = await game.text_channel.send(embed=lobby_embed,view=GameLobbyView(game,self))
        await context.channel.send("Game channels have been created.")

        # the following lines for testing purposes only
        await self.send_roles(game)
        # game.state = GameState.LEGISLATIVE_CHANCELLOR
        # # game.veto_power_enabled = False
        # await context.channel.send("Testing Legislative sequence", view=LegislativeSessionView(game,self))
    

    @commands.command(name="delgame")
    async def user_delete_game(self, context: Context):
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
    
    @commands.command(aliases=("leave","leaveall"))
    async def leave_game(self, context: Context):
        """Removes the command invoker from all active games they're in."""

        user = context.message.author

        for game in self.active_games.values():
            game: Game
            for player in game.players:
                if user.id == player.get_id():
                    game.players.remove(player)
                    await context.message.add_reaction("✅")
                    return
        
        # no active games with user found
        await context.message.reply(
            f"{user.mention}, you are not in any active games at the moment.")
        

    async def send_roles(self, game: Game):
        botmsg = await game.text_channel.send(
            "Now sending secret roles to all players. **Check your DMs!** :speech_balloon:")
        
        game.assign_roles()
        Hitler = game.get_hitler()
        Hitler_knows_fascists = True if len(game.players) < 7 else False
        fascist_team = game.get_team("Fascist")

        for player in game.players:
            user = self.bot.get_user(player.get_id())
            team = player.get_party()

            msg = f"{player.name}, your role is **{player.role}**.\nYou are a member of the **{team}** party."

            if team == "Fascist":
                fellow_fascists = [f.name for f in fascist_team if f.name != player.name]

                if player.role == "Hitler" and Hitler_knows_fascists:
                    msg += f"\nYour fellow fascist(s): {', '.join(fellow_fascists)}"
                
                elif player.role != "Hitler":
                    msg += f"\nYour fellow fascist(s): {', '.join(fellow_fascists)}"
                    msg += f"\n**{Hitler.name} is Hitler.**"
            
            await game.text_channel.send(msg)
        await botmsg.add_reaction("✅")
    
    def player_in_game(self, player_id: int):

        for game in self.active_games.values():
            game: Game
            for player in game.players:
                if player_id == player.get_id():
                    return True
        return False

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
    
    async def delete_game(self, game: Game):
        """Deletes a Game instance and the server modifications associated with it.
        
        This method was created to allow for deleting the Game instance programmatically
        rather than by a Discord user invoking the command by sending a message."""
        
        print("Game deleted programmatically.")
        await game.text_channel.delete()
        await game.category.delete()

        for game_id in self.active_games.keys():
            if game_id == game.get_id():
                self.active_games.pop(game_id)
                break

    
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
    
    def strip_spacing(self, input_string) -> str:
        """
        Returns input_string stripped of tab characters and line breaks so that
        each word is separated by a single space. This is useful for\
        eliminating the janky formatting that results when sending multiline\
        strings as Discord messages.
        """
        return re.sub(r'\s+', ' ', input_string)
        

class GameLobbyView(discord.ui.View):
    """Represents a Game Lobby View."""
    
    def __init__(self, game: Game, game_manager: SHGameMaintenance):
        super().__init__()
        self.game = game
        self.game_manager = game_manager

    
    @discord.ui.button(label="Join Lobby", style=discord.ButtonStyle.green)
    async def join_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_not_in_game = not self.game_manager.player_in_game(interaction.user.id)
        if player_not_in_game:
            self.game.add_player(interaction.user.id, interaction.user.name)
            embed = self.game.lobby_embed_msg.embeds[0]
            embed.set_field_at(1,name="Players in Lobby",value="\n".join([player.name for player in self.game.players]))
            await self.game.lobby_embed_msg.edit(embed=embed)
        else:
            msg = self.game_manager.strip_spacing(
                f"""{interaction.user.mention}, you are already in an active game.
                  Issue `.leave` to leave all active games.""")
            await interaction.response.send_message(msg, delete_after=DEL_AFTER_TIME)
    
        
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.red)
    async def leave_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_in_game = self.game_manager.player_in_game(interaction.user.id)
        if player_in_game:
            self.game.remove_player(interaction.user.id)
            embed = self.game.lobby_embed_msg.embeds[0]
            embed.set_field_at(1,name="Players in Lobby",value='\n'.join([player.name for player in self.game.players]))
            await self.game.lobby_embed_msg.edit(embed=embed)
        else:
            await interaction.response.send_message(
                content=f"{interaction.user.mention}, you are not in an active game or lobby.")
    
    @discord.ui.button(label="Abandon Lobby",style=discord.ButtonStyle.red)
    async def abandon_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.game.admin_id:
            await self.game_manager.delete_game(self.game)
        else:
            await interaction.response.send_message(
                content=f"{interaction.user.mention}, only the lobby host can abandon the lobby.",
                delete_after=DEL_AFTER_TIME)
    
    @discord.ui.button(label="Start Game",style=discord.ButtonStyle.blurple)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_is_host = interaction.user.id == self.game.admin_id
        min_players_met = len(self.game.players) >= Game.MIN_PLAYERS

        if user_is_host:
            if min_players_met:
                await interaction.response.send_message(content="Starting game!")
            else:
                await interaction.response.send_message(
                    content=f"Not enough players in lobby. A minimum of {Game.MIN_PLAYERS} players is needed to start a game.",delete_after=DEL_AFTER_TIME)
        else:
            await interaction.response.send_message(content=f"Only the lobby host (<@{self.game.admin_id}>) can start the game.", delete_after=DEL_AFTER_TIME)


class PresidentialPowerView(discord.ui.View):
    """Represents the View applied when a Presidential Power is being exercised."""

    def __init__(self, game: Game, pres_power: str):
        """Instantiates the Presidential Power View.
        
        Params:
        game: an instance of the Game class
        pres_power: a str representing the type of Presidential Power being used."""

        super().__init__()
        self.game = game
        self.pres_power = pres_power
        self.create_buttons()
    
    def create_buttons(self):
        """Creates the buttons for the View object depending on the\
            Presidential Power being exercised."""

        if self.pres_power == "Investigate Loyalty":
            players = self.game.get_investigatable_player_names()

            for p_name, p_id in players:
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(p_id),
                                        label=p_name)
                btn.callback = self.cb_investigate_loyalty
                self.add_item(btn)

        elif self.pres_power == "Call Special Election":
            players = self.game.get_special_election_candidates()

            for p_name, p_id in players:
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(p_id),
                                        label=p_name)
                btn.callback = self.cb_special_election
                self.add_item(btn)

        elif self.pres_power == "Policy Peek":
            btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                    label="Peek at Policies")
            btn.callback = self.cb_policy_peek
            self.add_item(btn)

        elif self.pres_power == "Execution":
            players = [(player.name,player.get_id()) for player
                        in self.game.get_players(include_president=False)]
        
            for p_name, p_id in players:
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(p_id),
                                        label=p_name)
                btn.callback = self.cb_execution
                self.add_item(btn)
        
        else:
            print(f"{self.pres_power} is not a recognized Presidential Power.")
            return False


    async def cb_investigate_loyalty(self,interaction: discord.Interaction):
        """A callback function for the Investigate Loyalty buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)
        
        if user_is_president:
            self.game.state = GameState.INVESTIGATION
            # the custom_id attribute of the button == the id of the player named on its label
            player_id = int(interaction.data.get('custom_id'))
            player_to_investigate = self.game.get_player(player_id)
            player_to_investigate.investigated = True
            president_name = interaction.user.name

            msg = (
                f"""
                **FOR THE EYES OF PRESIDENT {president_name.upper()} ONLY**\n
                President {president_name},\nYou chose to investigate {player_to_investigate.name}.
                They are a member of the {player_to_investigate.get_party()} party.\n
                {SHGameMaintenance.NO_SHARE_WARNING}
                """)
            
            # DM investigated player's party loyalty to President
            await interaction.user.send(msg, delete_after=DEL_AFTER_TIME)

            await interaction.message.channel.send(
                f"""President {interaction.user.name} chose to investigate the party loyalty of {player_to_investigate.name}!""")

    async def cb_special_election(self, interaction: discord.Interaction):
        """A callback function for the Call Special Election buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            self.game.state = GameState.SPECIAL_ELECTION
            # the custom_id attribute of the button == the id of the player named on its label
            player_id = int(interaction.data.get('custom_id'))
            nominated_pres = self.game.get_player(player_id)
            self.game.nominated_president = nominated_pres

            await interaction.message.channel.send(content=(
                f"""Incumbent President {self.game.incumbent_president.name} has nominated {nominated_pres.name}
                    to run in this upcoming Special Election!"""))

    async def cb_policy_peek(self, interaction: discord.Interaction):
        """A callback function for the Policy Peek buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            self.game.state = GameState.POLICY_PEEK

            p1, p2, p3 = self.game.policy_peek()
            pres_name = interaction.user.name

            msg = (f"""
                    **FOR THE EYES OF PRESIDENT {pres_name.upper()} ONLY**\n
                    You peek at the top 3 policy tiles in the deck and see the following policies: {p1}, {p2}, {p3}\n
                    {SHGameMaintenance.NO_SHARE_WARNING}
                    """)
            
            await interaction.user.send(content=msg,delete_after=DEL_AFTER_TIME)
            await interaction.message.channel.send(content=(
                f"""President {pres_name} takes the top 3 policy tiles in the\
                    policy tile deck and looks at them in secret before\
                    returning them to the top of the deck with\
                    their order unchanged."""))
            
            self.game.state = GameState.NOMINATION
        

    async def cb_execution(self, interaction: discord.Interaction):
        """A callback function for the Execution buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            self.game.state = GameState.EXECUTION
            pres_name = interaction.user.name
            player_id = int(interaction.data.get('custom_id'))
            chosen_player = self.game.get_player(player_id)
            chosen_player.dead = True

            async with interaction.message.channel.typing():
                await asyncio.sleep(2)
                await interaction.message.channel.send(
                    f"""President {pres_name} moves toward a nearby table and reaches for a revolver resting on it. They raise the gun and point it at {chosen_player.name}.""")
                
                await asyncio.sleep(4)
                await interaction.message.channel.send(
                    f"""President {pres_name} says aloud: "I formally execute {chosen_player.name}" and fires a shot killing them instantly.""")
                await asyncio.sleep(5)
                if chosen_player.role == "Hitler":
                    await interaction.message.channel.send(
                        f"""In the aftermath, documents are found on the dead body which positively identify the deceased as Adolf Hitler. Liberals win!""")
                    self.game.state = GameState.GAME_OVER
                else:
                    await interaction.message.channel.send(
                        f"""In the aftermath, documents are found on the dead body which reveal the deceased is **not** Adolf Hitler.""")
            

class LegislativeSessionView(discord.ui.View):
    """Represents the View applied when a legislative session is underway."""

    def __init__(self, game: Game, game_manager: SHGameMaintenance):
        """Instantiates the legislative session View."""
        super().__init__()
        self.game = game
        self.game_manager = game_manager
        self.create_buttons()
    
    def create_buttons(self):
        if self.game.state == GameState.LEGISLATIVE_PRESIDENT:
            print("Legislative view: pres")
            
            for i in range(1,4):
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(i),
                                        label=f"Discard Policy {i}")
                self.add_item(btn)


        elif self.game.state == GameState.LEGISLATIVE_CHANCELLOR:
            print("Legislative view: chanc")
            
            for i in range(1,3):
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=str(i),
                                        label=f"Discard Policy {i}")
                self.add_item(btn)
            
            if self.game.veto_power_enabled:
                btn = discord.ui.Button(style=discord.ButtonStyle.red,
                                        custom_id="veto",
                                        label="Request to Veto")
                btn.callback = self.cb_veto
                self.add_item(btn)
    
    def send_to_president(self):
        pass

    def send_to_chancellor(self):
        pass

    async def cb_veto(self, interaction: discord.Interaction):
        """A callback function for vetoing the agenda."""

        user_is_chancellor = interaction.user.id == self.game.incumbent_chancellor.get_id()

        if user_is_chancellor:
            pres = self.game_manager.bot.get_user(self.game.incumbent_president.get_id())

            view = discord.ui.View()
            btn1 = discord.ui.Button(style=discord.ButtonStyle.green,custom_id="agree",label="Agree to Veto")
            btn2 = discord.ui.Button(style=discord.ButtonStyle.red,custom_id="disagree",label="Refuse Veto")
            btn1.callback = self.process_president_veto
            btn2.callback = self.process_president_veto
            view.add_item(btn1)
            view.add_item(btn2)

            await self.game.text_channel.send(f"President {pres.mention}: Chancellor {interaction.user.name} wishes to veto this agenda. Do you agree?",
                            view=view,delete_after=DEL_AFTER_TIME)
            
    async def process_president_veto(self, interaction: discord.Interaction):
        """A callback function for processing the President's option to veto."""

        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            choice = interaction.data.get("custom_id")
            pres = interaction.user.name
            chancellor = self.game_manager.bot.get_user(self.game.incumbent_chancellor.get_id())

            if choice == "agree":
                await self.game.text_channel.send(
                    f"""President {pres} has agreed to the veto. No policy is enacted. The populace grows increasingly more frustrated. The election tracker advances by one.""")
                self.game.veto()
            elif choice == "disagree":
                await self.game.text_channel.send(
                    f"""President {pres} has refused the veto. Chancellor {chancellor.mention}, you must enact a policy.""")



async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))