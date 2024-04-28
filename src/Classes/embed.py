"Handles all Discord.Embed operations"

import discord
from Classes.game import Game

SH_ORANGE = discord.Color.from_rgb(242,100,74)

class GameLobbyEmbed(discord.Embed):
    """Represents a Game Lobby Discord.Embed object."""

    
    def __init__(self, game_id: str, lobby_owner_id: int):
        self.title = f"Secret Hitler Game Lobby (Game ID: {game_id})"
        self.color = SH_ORANGE
        self.owner_id = str(lobby_owner_id)
        self.players_in_lobby : list[str] = [self.owner_id]

        self.add_player(self.owner_id)

        self.add_field(name="Number of Players Required:",
                       value=f"{Game.MIN_PLAYERS}-{Game.MAX_PLAYERS}",
                       inline=False)
        
        self.add_field(name="Players in Lobby",value="")

        super().__init__(color=self.color, title=self.title,type="rich")
    
    def add_player(self, player_id: int):
        """Adds a player to the game lobby embed."""

        if len(self.players_in_lobby) == Game.MAX_PLAYERS: return

        player_id = str(player_id)
        
        if player_id not in self.players_in_lobby:
            self.players_in_lobby += player_id
            self.populate_player_list()
    
    def remove_player(self, player_id: int):
        """Removes a player from the game lobby embed."""

        player_id = str(player_id)

        if player_id in self.players_in_lobby:
            self.players_in_lobby.remove(player_id)
            self.populate_player_list()

    def populate_player_list(self):
        """Populates the list of players displayed on game lobby embed."""

        player_field = self.fields[1]
        player_names = []

        for player_id in self.players_in_lobby:
            player = discord.Client.get_user(int(player_id))

            if player:
                player: discord.User
                player_names.append(player.name)
        
        player_field.value = "\n".join(player_names)


class LicensingEmbed(discord.Embed):

    def __init__(self):

        copy = """*Secret Hitler* was created by Mike Boxleiter, Tommy Maranges, and Mac Schubert. 
        It is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/)."""

        super().__init__(color=SH_ORANGE,
                         title="Credits & License",
                         url="https://www.secrethitler.com/",
                         description=copy,
                         type="rich")
