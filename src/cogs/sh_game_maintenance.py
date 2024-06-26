"""
This module manages all Discord events and user input and modifies the
Game object associated with each event and user interaction.
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
import asyncio
import re
import json
import sys
sys.path.append('src')
from game import Game, GameState, Player

# Testing constants
DEL_AFTER_TIME = 10

# read in game-related messages to memory
with open(r"src\messages.json") as f:
    messages: dict = json.load(f)


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
                msg: str = messages["manage_game"]["already_host"]
                msg = msg.format(user=context.message.author.name)
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
        # else:
        #     # category exists
        #     for cat in guild.categories:
        #         if cat.name == category_name

        # await game.text_channel.send("Welcome to Secret Hitler!\nRules: https://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf")
        lobby_embed = self.create_lobby_embed(game)

        game.lobby_embed_msg = await game.text_channel.send(embed=lobby_embed,view=GameLobbyView(game,self))
        await context.channel.send("Game channels have been created.")

        # the following lines for testing purposes only

        # game.state = GameState.LEGISLATIVE_CHANCELLOR
        # # game.veto_power_enabled = False
        # await context.channel.send("Testing Legislative sequence", view=LegislativeSessionView(game,self))
        # await self.send_roles(game)
        await context.channel.send("Testing",view=PresidentialPowerView(game,self,SHGameMaintenance.SPECIAL_ELECTION))
    

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
        
        msg: str = messages["manage_game"]["not_host"]
        msg.format(user=context.message.author.name)
        await context.channel.send(msg)

    @commands.command(aliases=("terms","legal","license","licensing","tos"))
    async def send_licensing(self, context: Context):
        title = "Credits & License"
        url = "https://www.secrethitler.com/"
        color = Game.SH_ORANGE
        
        copy : str = messages["legal"]["license_terms"]
        terms_embed = discord.Embed(title=title,description=copy,url=url,color=color)

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
        msg: str = messages["manage_game"]["not_in_game"]
        msg.format(user=user.name)
        await context.message.reply(msg)
        
    async def send_roles(self, game: Game):

        botmsg = await game.text_channel.send(messages["roles"]["sending"])
        
        game.assign_roles()
        Hitler = game.get_hitler()
        Hitler_knows_fascists = True if len(game.players) < 7 else False
        fascist_team = game.get_team("Fascist")

        for player in game.players:
            player: Player
            user = self.bot.get_user(player.get_id())
            team = player.get_party()

            msg: str = messages["roles"]["default"]
            msg.format(user=player.name,role=player.role,party=team)
            
            if player.role == "Hitler" and Hitler_knows_fascists:
                fellow_fascists = [f.name for f in fascist_team if f.name != player.name]
                msg += f"\nYour fellow fascist(s): {', '.join(fellow_fascists)}"
            
            elif player.role != "Hitler" and team == "Fascist":
                fellow_fascists = [f.name for f in fascist_team if f.name != player.name]
                msg += f"\nYour fellow fascist(s): {', '.join(fellow_fascists)}"
                msg += f"\n**{Hitler.name} is Hitler.**"

            await game.text_channel.send(msg)
            # await user.send(msg)
        await botmsg.add_reaction("✅")

    async def game_over(self, game: Game):
        await game.text_channel.send(
            "Game over!"
        )

    async def start_voting(self, game: Game):
        
        msg : str = messages["election"]["announce_start"]
        await game.text_channel.send(msg)
        
        msg : str = messages["election"]["announce_candidates"]
        msg.format(pres=game.nominated_president.name,
                   chanc=game.nominated_chancellor.name)
        
        await game.text_channel.send(msg,view=VotingView(game,self))
    
    async def start_nomination(self, game: Game, pres: Player):
        game.state = GameState.NOMINATION
        game.nominated_president = pres
        user = self.bot.get_user(pres.get_id())
        
        await game.text_channel.send(
            f"Presidential nominee {user.mention}, nominate a player to be Chancellor.",
            view=NominationView(game,self))
        
        

    async def start_election(self):
        pass

    async def start_legislative_pres(self, game: Game):
        game.state = GameState.LEGISLATIVE_PRESIDENT

        # public announcement
        msg : str = messages['legislative_pres']["pres_selecting"]
        msg.format(pres=game.incumbent_president.name)
        await game.text_channel.send(msg)

        # DM President drawn policy tiles
        msg2 : str = messages["legislative_pres"]["3_policies"]
        pres = self.bot.get_user(game.incumbent_president.get_id())
        await pres.send(msg2,view=LegislativeSessionView(game,self))


    async def start_legislative_chanc(self, game: Game):
        game.state = GameState.LEGISLATIVE_CHANCELLOR

        # public announcement
        msg : str = messages["legislative_chanc"]["chanc_selecting"]
        msg.format(chanc=game.incumbent_chancellor.name)
        await game.text_channel.send(msg)

        # DM Chancellor policy tiles
        msg2 : str = messages["legislative_chanc"]["2_policies"]
        msg2.format(pres=game.incumbent_president.name)
        chanc = self.bot.get_user(game.incumbent_chancellor.get_id())
        await chanc.send(msg2, view=LegislativeSessionView(game,self))

    async def start_veto(self):
        pass

    async def start_investigate_loyalty(self):
        pass

    async def start_special_election(self):
        pass

    async def start_policy_peek(self):
        pass

    async def start_execution(self):
        pass

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
            msg: str = messages["manage_game"]["already_in_game"]
            msg.format(user=interaction.user.name)
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
            msg: str = messages["manage_game"]["not_in_lobby"]
            msg.format(user=interaction.user.name)
            await interaction.response.send_message(msg)
    
    @discord.ui.button(label="Abandon Lobby",style=discord.ButtonStyle.red)
    async def abandon_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.game.admin_id:
            await interaction.message.edit(view=None)
            await self.game_manager.delete_game(self.game)
        else:
            msg: str = messages["manage_game"]["cannot_abandon"]
            msg.format(user=interaction.user.name)
            await interaction.response.send_message(msg,delete_after=DEL_AFTER_TIME)
    
    @discord.ui.button(label="Start Game",style=discord.ButtonStyle.blurple)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_is_host = interaction.user.id == self.game.admin_id
        min_players_met = len(self.game.players) >= Game.MIN_PLAYERS

        if user_is_host:
            if min_players_met:
                await interaction.message.edit(view=None)
                await interaction.response.send_message(content="Starting game!")
            else:
                msg: str = messages["manage_game"]["not_enough_players"]
                msg.format(minimum=Game.MIN_PLAYERS)
                await interaction.response.send_message(msg,delete_after=DEL_AFTER_TIME)
        else:
            msg: str = messages["manage_game"]["cannot_start"]
            msg.format(admin=self.game.admin_id)
            await interaction.response.send_message(msg, delete_after=DEL_AFTER_TIME)


class PresidentialPowerView(discord.ui.View):
    """Represents the View applied when a Presidential Power is being exercised."""

    def __init__(self, game: Game, game_manager: SHGameMaintenance,
                 pres_power: str):
        """Instantiates the Presidential Power View.
        
        Params:
        game: an instance of the Game class
        pres_power: a str representing the type of Presidential Power being used."""

        super().__init__()
        self.game = game
        self.game_manager = game_manager
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
            print("here 1")
            players = self.game.get_special_election_candidates()

            for p_name, p_id in players:
                print("here 2")
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
            await interaction.message.edit(view=None)
            self.game.state = GameState.INVESTIGATION
            # the custom_id attribute of the button == the id of the player named on its label
            player_id = int(interaction.data.get('custom_id'))
            player_to_investigate = self.game.get_player(player_id)
            player_to_investigate.investigated = True
            president_name = interaction.user.name

            msg : str = messages["investigate"]["pres_msg"]
            msg.format(pres=president_name,
                       investigated=player_to_investigate.name,
                       investigated_party=player_to_investigate.get_party(),
                       warning=messages["warning"]["no_share"])
            
            # DM investigated player's party loyalty to President
            await interaction.user.send(msg, delete_after=DEL_AFTER_TIME)

            msg2 : str = messages["investigate"]["announce_choice"]
            msg2.format(pres=president_name,investigated=player_to_investigate.name)
            await interaction.message.channel.send(msg2)

    async def cb_special_election(self, interaction: discord.Interaction):
        """A callback function for the Call Special Election buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            await interaction.message.edit(view=None)
            self.game.state = GameState.SPECIAL_ELECTION
            # the custom_id attribute of the button == the id of the player named on its label
            player_id = int(interaction.data.get('custom_id'))
            nominated_pres = self.game.get_player(player_id)
            self.game.nominated_president = nominated_pres

            msg : str = messages["special_election"]["announcement"]
            msg.format(incumbent_pres=self.game.incumbent_president.name,
                       nominated_pres=self.game.nominated_president.name)
            
            await interaction.message.channel.send(msg)

            # prompt new Presidential nominee
            msg2 : str = messages["special_election"]["prompt_pres"]
            msg2.format(nominated_pres=self.game.nominated_president.name)
            await interaction.message.channel.send(msg2,view=NominationView(self.game,self.game_manager))

    async def cb_policy_peek(self, interaction: discord.Interaction):
        """A callback function for the Policy Peek buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            await interaction.message.edit(view=None)
            self.game.state = GameState.POLICY_PEEK

            p1, p2, p3 = self.game.policy_peek()
            pres_name = interaction.user.name

            msg : str = messages["policy_peek"]["pres_msg"]
            msg.format(pres=pres_name,
                       p1=p1,
                       p2=p2,
                       p3=p3,
                       warning=messages["warning"]["no_share"])

            await interaction.user.send(msg,delete_after=DEL_AFTER_TIME)
            
            msg2 : str = messages["policy_peek"]["public_msg"]
            msg2.format(pres=pres_name)
            
            await interaction.message.channel.send(msg2)
            
            self.game.state = GameState.NOMINATION
        

    async def cb_execution(self, interaction: discord.Interaction):
        """A callback function for the Execution buttons."""
        
        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            await interaction.message.edit(view=None)
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
                    self.game.state = GameState.GAME_OVER
                    msg : str = messages["manage_game"]["liberals_win_hitler"]
                    await interaction.message.channel.send(msg)
                    
                else:
                    await interaction.message.channel.send(messages["manage_game"]["hitler_not_executed"])


class NominationView(discord.ui.View):
    """Represents the View applied during the nomination stage."""

    def __init__(self, game: Game, game_manager: SHGameMaintenance):
        super().__init__()
        self.game = game
        self.game_manager = game_manager
        self.create_buttons()

    def create_buttons(self):
        eligible = self.game.get_chancellor_candidates()

        for i, player in enumerate(eligible):
            player: Player
            btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                    custom_id=str(player.get_id()),
                                    label=player.name)
            btn.callback = self.nominate
            self.add_item(btn)
    
    async def nominate(self, interaction: discord.Interaction):
        user_is_pres_nom = self.game.is_nominated_president(interaction.user.id)

        if user_is_pres_nom:
            self.game.nominated_chancellor : Player = self.game.get_player(int(interaction.data.get('custom_id')))
            await interaction.message.edit(view=None)

            msg : str = messages["nomination"]["chanc_nominated"]
            msg.format(nominated_pres=self.game.nominated_president.name,
                       nominated_chanc=self.game.nominated_chancellor.name)
            
            await self.game.text_channel.send(msg)
            await self.game_manager.start_voting(self.game)

        else:
            interaction.response(
                f"{interaction.user.mention}, only the nominated President can nominate a Chancellor.")


class VotingView(discord.ui.View):
    """Represents the View applied during the voting stage."""

    def __init__(self, game: Game, game_manager: SHGameMaintenance):
        super().__init__()
        self.game = game
        self.game_manager = game_manager
        self.create_buttons()

    def create_buttons(self):
        
        yes = discord.ui.Button(style=discord.ButtonStyle.green,
                                custom_id="ja",
                                label="Ja")
        no = discord.ui.Button(style=discord.ButtonStyle.red,
                                custom_id="nein",
                                label="Nein")
        yes.callback = self.process_vote
        no.callback = self.process_vote
        self.add_item(yes)
        self.add_item(no)

    async def process_vote(self, interaction: discord.Interaction):

        vote = interaction.data.get('custom_id')
        res = self.game.vote(interaction.user.id,vote)
        chn = self.game.text_channel

        if res == 0:
            msg : str = messages["election"]["vote_recorded"]
            msg.format(user=interaction.user.mention)
            await chn.send(msg,delete_after=DEL_AFTER_TIME)
        
        elif res == 1:
            msg : str = messages["election"]["vote_cast"]
            msg.format(user=interaction.user.mention)
            await chn.send(msg,delete_after=DEL_AFTER_TIME)
        
        elif res == 2:
            await interaction.message.edit(view=None)
            await chn.send(messages["election"]["all_votes_in"])
            
            vote_passed = self.game.tally_votes()

            show_votes = ""

            for player_id, vote in self.game.votes.items():
                player = self.game.get_player(player_id)
                show_votes += f"{player.name}: {vote}\n"
            
            
            async with chn.typing():
                await chn.send("Tallying votes... :abacus:")
                await asyncio.sleep(1)
                await chn.send(show_votes)

                if vote_passed:

                    msg : str = messages["election"]["passed"]
                    msg.format(pres=self.game.incumbent_president.name,
                               chanc=self.game.incumbent_chancellor.name)
                    await chn.send(msg)
                    
                    self.game_manager.start_legislative_pres()
                
                else:
                    msg : str = messages["election"]["failed"]
                    msg.format(pres=self.game.nominated_president.name,
                               chanc=self.game.nominated_chancellor.name)
                    await chn.send(msg)
                    
                    pres_index = self.game.rotate_president()
                    self.game_manager.start_nomination(self.game,self.game.players[pres_index])
            
        self.game.votes.clear()


class LegislativeSessionView(discord.ui.View):
    """Represents the View applied when a legislative session is underway."""

    def __init__(self, game: Game, game_manager: SHGameMaintenance,
                veto_failed = False):
        """Instantiates the legislative session View."""

        super().__init__()
        self.game = game
        self.game_manager = game_manager
        self.veto_failed = veto_failed
        self.create_buttons()
    
    def create_buttons(self):
        if self.game.state == GameState.LEGISLATIVE_PRESIDENT:
            print("Legislative view: pres")
            
            self.game.policies_in_play = self.game.policy_tile_deck[:3]

            for index, tile in enumerate(self.game.policies_in_play):
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=f"{tile}{index}", # eg. "Fascist1"
                                        label=f"Discard {tile} Policy")
                btn.callback = self.pass_to_chancellor
                self.add_item(btn)


        elif self.game.state == GameState.LEGISLATIVE_CHANCELLOR:
            print("Legislative view: chanc")
            
            # create a discard button for each tile
            for index, tile in enumerate(self.game.policies_in_play):
                btn = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                        custom_id=f"{tile}{index}",
                                        label=f"Discard {tile} Policy")
                btn.callback = self.cb_enact_policy
                self.add_item(btn)
            
            # add veto button if applicable
            if self.game.veto_power_enabled and not self.veto_failed:
                btn = discord.ui.Button(style=discord.ButtonStyle.red,
                                        custom_id="veto",
                                        label="Request to Veto")
                btn.callback = self.cb_veto
                self.add_item(btn)
        else:
            print(self.game.state.value, " GameState not a recognized View.")
    
    def send_to_president(self):
        pass

    async def pass_to_chancellor(self, interaction: discord.Interaction):

        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            await interaction.message.edit(view=None)

            # ignore last index position ("Fascist1" -> "Fascist")
            discarded = interaction.data.get('custom_id')[:-1]
            self.game.policies_in_play.remove(discarded)
            self.game.discard_policy_tile(discarded)

            await self.game_manager.start_legislative_chanc(self.game)

    async def cb_veto(self, interaction: discord.Interaction):
        """A callback function for vetoing the agenda."""

        user_is_chancellor = interaction.user.id == self.game.incumbent_chancellor.get_id()

        if user_is_chancellor:
            await interaction.message.edit(view=None)
            self.game.state = GameState.VETO
            pres = self.game_manager.bot.get_user(self.game.incumbent_president.get_id())

            view = discord.ui.View()
            btn1 = discord.ui.Button(style=discord.ButtonStyle.green,custom_id="agree",label="Agree to Veto")
            btn2 = discord.ui.Button(style=discord.ButtonStyle.red,custom_id="disagree",label="Refuse Veto")
            btn1.callback = self.cb_process_president_veto
            btn2.callback = self.cb_process_president_veto
            view.add_item(btn1)
            view.add_item(btn2)

            await self.game.text_channel.send(f"President {pres.mention}: Chancellor {interaction.user.name} wishes to veto this agenda. Do you agree?",
                            view=view,delete_after=DEL_AFTER_TIME)
            
    async def cb_process_president_veto(self, interaction: discord.Interaction):
        """A callback function for processing the President's option to veto."""

        user_is_president = self.game.is_president(interaction.user.id)

        if user_is_president:
            await interaction.message.edit(view=None)
            discard = interaction.data.get("custom_id")
            pres = interaction.user.name
            chancellor = self.game_manager.bot.get_user(self.game.incumbent_chancellor.get_id())

            if discard == "agree":
                msg : str = messages["veto"]["pres_accepts"]
                msg.format(pres=pres)
                await self.game.text_channel.send(msg)
                self.game.veto()
                self.game.state = GameState.NOMINATION
            
            elif discard == "disagree":
                self.game.state = GameState.LEGISLATIVE_CHANCELLOR
                print("Pres refused veto. Return to Chancellor decision.")

                msg : str = messages["veto"]["pres_declines"]
                msg.format(pres=pres,chanc=chancellor.name)
                await self.game.text_channel.send(msg)
                
                msg : str = messages["veto"]["pres_declines_chanc_msg"]
                msg.format(pres=pres)
                await chancellor.send(msg, view=LegislativeSessionView(game=self.game,
                                                                       game_manager=self.game_manager,
                                                                       veto_failed=True))
    
    async def cb_enact_policy(self, interaction: discord.Interaction):
        """A callback function for enacting a policy."""
        user_is_chancellor = self.game.is_chancellor(interaction.user.id)

        if user_is_chancellor:
            await interaction.message.edit(view=None)
            discard = interaction.data.get('custom_id')[:-1]
            self.game.policies_in_play.remove(discard)
            self.game.discard_policy_tile(discard)

            self.game.enact_policy(self.game.policies_in_play[0])
            
            self.game_manager.start_nomination(self.game,)


async def setup(bot):
    await bot.add_cog(SHGameMaintenance(bot))