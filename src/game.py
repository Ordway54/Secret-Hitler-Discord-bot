"""
This module contains all of the game logic for playing Secret Hitler.
"""

import random
from enum import Enum
from config import configuration
import discord

class Game:
    """Represents a game of Secret Hitler."""

    LICENSE_TERMS = (
            """
            Secret Hitler was created by Mike Boxleiter, Tommy Maranges,\
            and Mac Schubert.\n
            Secret Hitler is licensed under a Creative Commons\
            Attribution-NonCommercial-ShareAlike 4.0\
            International License.
            This license permits the copying and\
            redistribution of Secret Hitler in any medium or format for\
            non-commercial purposes.\n

            Visit http://www.secrethitler.com/ to learn more.
            """
            )

    SH_ORANGE = discord.Color.from_rgb(242,100,74)
    MIN_PLAYERS = 5
    MAX_PLAYERS = 10

    def __init__(self, game_id, admin_id):
        self.players = []
        self.dead_players = []

        self.votes = {}

        self.fascist_policies_enacted = 0
        self.liberal_policies_enacted = 0

        self.president_rotation_index : int = 0
        self.incumbent_president : Player = None
        # self.nominated_president : Player = None
        self.president : Player = None
        self.previous_president : Player = None

        # self.nominated_chancellor : Player = None
        self.incumbent_chancellor : Player = None
        self.previous_chancellor : Player = None

        self.state = GameState.LOBBY
        self.admin_id = admin_id
        self.game_id = game_id
        self.max_players = 10
        self.min_players = 5
        self.veto_power_enabled = False

        self.policy_tile_deck = ['Liberal','Liberal','Liberal','Liberal',
                                'Liberal','Liberal','Fascist','Fascist',
                                'Fascist','Fascist','Fascist','Fascist',
                                'Fascist','Fascist','Fascist','Fascist',
                                'Fascist']
        
        self.discarded_policy_tiles = []
        self.election_tracker = 0

        # server modifications
        self.category : discord.CategoryChannel = None
        self.text_channel : discord.TextChannel = None
        self.lobby_embed_msg : discord.Message = None
        
        self.add_player(admin_id,'freaky Mike')

    def add_player(self, player_id: int, player_name: str):
        """Adds a player to the Game."""

        player_count = len(self.players)

        if player_count == self.max_players:
            return False
        else:
            self.players.append(Player(player_id,player_name))
            return True
    
    def remove_player(self, player_id):
        """Removes a player from the Game."""

        for player in self.players:
            player: Player
            if player_id == player.get_id():
                self.players.remove(player)
                return
        return False
    
    def get_player(self, player_id):
        """Returns a Player instance matching player_id."""

        for player in self.players:
            player: Player
            if player_id == player.get_id():
                return player
        return None
    
    def get_players(self):
        return self.players
    
    def get_id(self):
        return self.game_id
    
    def has_player(self, player_id):
        """Returns True if player_id matches a player in the Game."""

        for player in self.players:
            if player_id == player.get_id():
                return True
        return False
    
    def start(self):
        """
        Starts a game of Secret Hitler by shuffling player seats,\
        shuffling the policy tile deck, and randomly assigning a role\
        to each player.
        """
        self.state = GameState.GAME_STARTING

        if len(self.players) < self.max_players:
            print("Game not started. Not enough players.")
            return False
        
        random.shuffle(self.players)
        random.shuffle(self.policy_tile_deck)

        roles = configuration[self.max_players]["roles"]
        random.shuffle(roles)

        # assign player roles
        for i in range(self.max_players):
            player: Player = self.players[i]
            player.role = roles[i]

        # select first Presidential candidate
        self.president = self.players[0]

        self.state = GameState.NOMINATION
    
    def destroy(self):
        """Deletes the game instance and undoes all changes to Discord server."""
        # do stuff here
        # delete all temporary text channels associated with Game
        del self

    def rotate_president(self):
        """Assigns the role of nominated President to the next player in line."""

        if self.president_rotation_index == (len(self.players) - 1):
            self.president_rotation_index = 0
        else:
            self.president_rotation_index += 1

    def nominate_chancellor(self, player_id):

        self.state = GameState.NOMINATION

        if player_id != self.previous_president and player_id != self.previous_chancellor:
            return True
        elif (player_id == self.previous_president) and (len(self.players) == 5):
            return True
        elif player_id == self.previous_president:
            return False
        elif player_id == self.previous_chancellor:
            return False
        
        return True

    def vote(self, player_id: int, vote: str):

        # disallow changes in vote
        for id, vote in self.votes.items():
            if id == player_id:
                return False

        if len(self.votes) == len(self.players):
            # all votes are in
            return False
        
        self.votes[player_id] = vote
        return True
    
    def tally_votes(self):
        yes_votes = 0
        no_votes = 0

        for _, vote in self.votes.items():
            if vote == 'yes':
                yes_votes += 1
            else:
                no_votes += 1
               
        if yes_votes > no_votes:
            self.reset_election_tracker()
            self.state = GameState.LEGISLATIVE_PRESIDENT
            
        else:
            country_in_chaos = self.advance_election_tracker()
            if country_in_chaos:
                self.force_next_policy()
                self.reset_election_tracker()
                self.reset_term_limits()
            
            self.state = GameState.NOMINATION
            self.rotate_president()
            
    def reset_election_tracker(self):
        """Resets the election tracker to 0."""
        self.election_tracker = 0
    
    def advance_election_tracker(self, n=1) -> bool:
        """Advances the election tracker by n (defaults to 1) and returns\
        True if the election tracker == 3. Otherwise returns False."""
        
        self.election_tracker += n

        if self.election_tracker == 3:
            return True
        return False

    def reset_term_limits(self):
        self.previous_chancellor = None
        self.previous_president = None
    
    def enable_veto_power(self):
        """Enables veto power if 5 or more Fascist policies have been enacted."""
        if self.fascist_policies_enacted >= 5:
            self.veto_power_enabled = True
    
    def veto(self, president_veto: bool, chancellor_veto: bool, policy_tiles: list):
        """Allows the agenda to be veto'd if both President and Chancellor agree."""
        
        if self.veto_power_enabled:
            if all((president_veto, chancellor_veto)):
                # veto passes
                for tile in policy_tiles:
                    self.discarded_policy_tiles.append(tile)
                
                country_in_chaos = self.advance_election_tracker()
                if country_in_chaos:
                    self.force_next_policy()
                    self.reset_election_tracker()
                    self.reset_term_limits()
                    self.check_for_win()
                
                self.rotate_president()

            else:
                # veto fails
                return False
        else:
            # veto power is no in effect yet
            return False

    def election(self):
        self.state = GameState.ELECTION


    def force_next_policy(self):
        """Enacts the next policy in the deck due to 3 consecutive failed elections."""

        if len(self.policy_tile_deck) >= 3:
            top_policy = self.policy_tile_deck.pop(0)

            if top_policy == "Fascist":
                self.fascist_policies_enacted += 1
                self.enable_veto_power()
            else:
                self.liberal_policies_enacted += 1

            if len(self.policy_tile_deck) < 3:
                self.refill_policy_tile_deck()

    def refill_policy_tile_deck(self):
        """Refills the policy tile deck if there are insufficient policy tiles."""

        if len(self.policy_tile_deck) < 3:
            for tile in self.discarded_policy_tiles:
                self.policy_tile_deck.append(tile)
            self.discarded_policy_tiles.clear()
            random.shuffle(self.policy_tile_deck)

    def draw_policy_tile(self):
        """Draws the top policy tile from the policy tile deck."""
        if len(self.policy_tile_deck) > 0:
            return self.policy_tile_deck[0]

    def check_for_win(self) -> (bool,str):
        """Checks possible win conditions and returns True if the game is over.\
            False otherwise."""

        # check if game over based on enacted policy counts
        if self.liberal_policies_enacted >= 5 and self.fascist_policies_enacted < 6:
            self.state = GameState.GAME_OVER
            return (True, "Game Over. The Liberals win!")
        elif self.fascist_policies_enacted >= 6 and self.liberal_policies_enacted < 5:
            self.state = GameState.GAME_OVER
            return (True, "Game Over. The Fascists win!")
        
        
        for player in self.players:
            player: Player
            
            if player.role == "Hitler":
                # check if Hitler has been assassinated
                if player.dead:
                    self.state = GameState.GAME_OVER
                    return (True,"Hitler has been assassinated! Game Over. The Liberals win!")

                # check if Hitler has been elected Chancellor
                elif (player.get_id() == self.incumbent_chancellor) and self.fascist_policies_enacted > 3:
                    self.state = GameState.GAME_OVER
                    return (True, "Hitler has been elected Chancellor! Game Over. The Fascists win!")
        
        return False

    def investigate_loyalty(self, player_id):
        """Returns the Party Membership of the Player with player_id."""

        player_to_investigate = self.get_player(player_id)
        player_to_investigate: Player

        if player_to_investigate.investigated:
            return False

        return player_to_investigate.get_party()
    
    def call_special_election(self, player_id):

        if player_id != self.incumbent_president.get_id():
            return False
        
        # have President select next President
        # start election as normal

    def policy_peek(self):

        if len(self.policy_tile_deck) < 3:
            self.refill_policy_tile_deck()

        
        policy_1 = self.policy_tile_deck[0]
        policy_2 = self.policy_tile_deck[1]
        policy_3 = self.policy_tile_deck[2]

        return policy_1, policy_2, policy_3
    
    def execution(self, player_id: int):

        # prompt President to choose a player to execute
        
        player_to_execute = self.get_player(player_id)
        player_to_execute.dead = True

        self.dead_players = [player for player in self.players if player.dead]





class Player:
    """Represents a Player in a Secret Hitler game."""

    def __init__(self, player_id: int, player_name: str):
        self.player_id = player_id
        self.name = player_name
        self.role = None
        self.dead = False
        self.investigated = False
    
    def get_party(self):
        if self.role == "Fascist" or self.role == "Hitler":
            return "Fascist"
        else:
            return "Liberal"
    
    def get_id(self):
        """Returns the Player's Discord ID."""

        return self.player_id

class GameState(Enum):
    LOBBY = 1
    GAME_STARTING = 2
    NOMINATION = 3
    ELECTION = 4
    LEGISLATIVE_PRESIDENT = 5
    LEGISLATIVE_CHANCELLOR = 6
    VETO = 7
    INVESTIGATION = 8
    SPECIAL_ELECTION = 9
    POLICY_PEEK = 10
    EXECUTION = 11
    GAME_OVER = 12