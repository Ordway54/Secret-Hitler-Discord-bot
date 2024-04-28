class Player:
    """Represents a Player in a Secret Hitler game."""

    def __init__(self, discord_id: int, discord_name: str):
        self.id = discord_id
        self.name = discord_name
        self.role = None
        self.dead = False
        self.investigated = False
        self.term_limited = False
    
    def get_party(self):
        if self.role is not None:
            if self.role == "Fascist" or self.role == "Hitler":
                return "Fascist"
            else:
                return "Liberal"
    
    def get_id(self):
        """Returns the Player's Discord ID."""

        return self.id
    
    def is_dead(self):
        return self.dead
    
    def is_term_limited(self):
        return self.term_limited