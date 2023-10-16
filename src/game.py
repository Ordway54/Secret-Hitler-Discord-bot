import random
from enum import Enum
from config import configuration

class Game:
    """Represents a game of Secret Hitler."""

    def __init__(self, channel_id, game_id, admin_id, max_players):
        self.players = []
        self.dead_players = []
        self.state = GameState.GAME_STARTING
        self.admin_id = admin_id
        self.game_id = game_id
        self.channel_id = channel_id
        self.max_players = max_players
        self.policy_tiles = ['Liberal','Liberal','Liberal','Liberal',
                             'Liberal','Liberal','Fascist','Fascist',
                             'Fascist','Fascist','Fascist','Fascist',
                             'Fascist','Fascist','Fascist','Fascist',
                             'Fascist']
        self.discarded_policy_tiles = []
        self.failed_elections = 0
        
        
        random.shuffle(self.policy_tiles)

    def get_player_count(self) -> int:
        return len(self.players)

    def add_player(self, player_id):
        """Adds a player to the Game."""

        player_count = self.get_player_count()

        if player_count == self.max_players:
            return False
        else:
            self.players.append(Player(player_id))
            return True
    
    def remove_player(self, player_id):
        """Removes a player from the Game."""

        player = Player(player_id)

        if player in self.players:
            self.players.remove()
        else:
            return False
        
    def assign_player_roles(self):
        """Assigns roles to all Players."""
        roles = configuration[self.max_players]["roles"]
        
        if len(self.players) == self.max_players:
            for player in self.players:
                player: Player

                role = random.choice(roles)
                player.role = role
                roles.remove(role)
                
        return False

    def next_president(self):
        """Assigns the role of President to the next player."""
        pass


class Player:
    """Represents a Player in a Secret Hitler game."""

    def __init__(self, player_id):
        self.player_id = player_id
        self.role = None
        self.dead = False
        self.is_president = False
        self.is_chancellor = False
    
    def get_party(self):
        if self.role == "Fascist" or self.role == "Hitler":
            return "Fascist"
        else:
            return "Liberal"
    
    def get_id(self):
        """Returns the Player's id."""

        return self.player_id

class GameState(Enum):
    GAME_STARTING = 1
    NOMINATION = 2
    ELECTION = 3
    LEGISLATIVE_PRESIDENT = 4
    LEGISLATIVE_CHANCELLOR = 5
    VETO = 6
    INVESTIGATION = 7
    SPECIAL_ELECTION = 8
    POLICY_PEEK = 9
    EXECUTION = 10
    GAME_OVER = 11