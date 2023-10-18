import random
from enum import Enum
from config import configuration

class Game:
    """Represents a game of Secret Hitler."""

    def __init__(self, channel_id, game_id, admin_id, max_players):
        self.players = []
        self.dead_players = []
        self.liberals = []
        self.fascists = []

        self.votes = {}

        self.fascist_policies_enacted = 0
        self.liberal_policies_enacted = 0

        self.incumbent_president_id = 0
        self.nominated_president_id = 0
        self.president = None
        self.previous_president_id = 0

        self.nominated_chancellor_id = 0
        self.incumbent_chancellor_id = None
        self.previous_chancellor_id = 0

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
        self.election_tracker = 0
        
        
        random.shuffle(self.policy_tiles)
        self.add_player(admin_id)

    def add_player(self, player_id):
        """Adds a player to the Game."""

        player_count = len(self.players)

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
    
    def get_player(self, player_id):
        """Returns a Player instance matching the player_id, if found."""

        for player in self.players:
            player: Player
            if player_id == player.get_id():
                return player
        return None
    
    def has_player(self, player_id):
        """Returns True if player_id matches a player in the Game."""

        for player in self.players:
            if player_id == player.get_id():
                return True
        return False
    
    def start_game(self):
        
        if len(self.players) < self.max_players:
            return False
        
        # shuffle player seats
        random.shuffle(self.players)

        # shuffle roles
        roles = configuration[self.max_players]["roles"]

        # assign player roles
        for i in range(self.max_players):
            player = self.players[i]
            player.role = roles[i]

        # select first Presidential candidate
        self.president = self.players[0]
    
    def destroy(self):
        """Deletes the game instance and undoes all changes to Discord server."""
        pass


    def next_president(self):
        """Assigns the role of nominated President to the next player."""

        if self.incumbent_president_id >= len(self.players - 1):
            self.incumbent_president_id = 0
        else:
            self.incumbent_president_id += 1

        self.previous_president_id = self.incumbent_president_id

    def nominate_chancellor(self, player_id):

        self.state = GameState.NOMINATION

        # check if previous President has been nominated Chancellor
        if player_id == self.previous_president_id:
            # term-limited
            return False
        
        # check if previous Chancellor has been nominated Chancellor again
        if player_id == self.previous_chancellor_id:
            # term-limited
            return False
        
        # nomination OK
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
            elif vote == 'no':
                no_votes += 1
               
        if yes_votes > no_votes:
            self.election_tracker = 0
            pass
            
        else:
            self.election_tracker += 1

            if self.election_tracker == 3:
                self.force_next_policy()
            
            self.next_president()
            


    def election(self):
        self.state = GameState.ELECTION

    def force_next_policy(self):
        """Enacts the next policy in the deck due to 3 consecutive failed elections."""

        top_policy = self.policy_tiles.pop(0)

        if top_policy == "Fascist":
            self.fascist_policies_enacted += 1
        else:
            self.liberal_policies_enacted += 1
        
        self.election_tracker = 0

    def draw_policy(self):
        """Draws the top policy tile from the policy tile deck."""

        # check if deck has sufficient tiles
        if len(self.policy_tiles) == 0:
            self.policy_tiles = self.discarded_policy_tiles.copy()
            self.discarded_policy_tiles.clear()
            random.shuffle(self.policy_tiles)
        
        
        self.policy_tiles = self.discarded_policy_tiles.copy()

    
    def check_for_win(self):
        
        if self.liberal_policies_enacted >= 5 and self.fascist_policies_enacted < 6:
            self.state = GameState.GAME_OVER
            return
        elif self.fascist_policies_enacted >= 6 and self.liberal_policies_enacted < 5:
            self.state = GameState.GAME_OVER
            return
        
        
        for player in self.players:
            player: Player
            
            # check if Hitler has been assassinated
            if player.role == "Hitler":
                if player.dead:
                    # Liberals win
                    self.state = GameState.GAME_OVER
            
                elif player.get_id() == self.incumbent_chancellor_id and self.fascist_policies_enacted > 3:
                    # Fascists win
                    self.state = GameState.GAME_OVER
        

class Player:
    """Represents a Player in a Secret Hitler game."""

    def __init__(self, player_id):
        self.player_id = player_id # will be user's Discord ID
        self.role = None
        self.dead = False
    
    def get_party(self):
        if self.role == "Fascist" or self.role == "Hitler":
            return "Fascist"
        else:
            return "Liberal"
    
    def get_id(self):
        """Returns the Player's Discord ID."""

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