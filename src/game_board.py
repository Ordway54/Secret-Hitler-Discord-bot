"""
This module manages all game board management operations.
"""

from PIL import Image, ImageDraw
from game import Game

board = Image.open(r'C:\Users\xxrus\OneDrive\Documents\Python scripts\Secret Hitler bot\images\9_10p fascist track.png')
# board2 = Image.open(r'C:\Users\xxrus\OneDrive\Documents\Python scripts\Secret Hitler bot\images\fascist board 2.png')
f_tile = Image.open(r'C:\Users\xxrus\OneDrive\Documents\Python scripts\Secret Hitler bot\images\fascist tile.png')

# fpos = {
#     1: (410,400),
#     2: (1010,400),
#     3: (1610,400),
#     4: (2210,400),
#     5: (2810,400),
#     6: (3410,400)
# }

# lpos = {
#     1: (690,380),
#     2: (1290,380),
#     3: (1890,380),
#     4: (2490, 380),
#     5: (3090, 380)
# }

# for v in fpos.values():
#     board.paste(f_tile,box=v)


# # liberal track tile positions
# # 1 (690,380)
# # 2 (1290,380)
# # 3 (1890,380)
# # 4 (2490, 380)
# # 5 (3090, 380)

# board.show()



class GameBoard:
    """Represents a Secret Hitler game board/track."""

    ELEC_TRACKER_POS = {
            1: (1447,1211,1591,1355),
            2: (1847,1211,1991,1355),
            3: (2252,1211,2396,1355),
            4: (2652,1211,2796,1355),
        }

    def __init__(self, game: Game):
        self.game = game
        self.liberal_track = [0,0,0,0,0]
        self.fascist_track = [0,0,0,0,0,0]
        self.liberal_track_img = Image.open('images\liberal track.png')
        self.draw_election_tracker_token(1)
        
        
        if len(self.game.players) in (5,6):
            self.fascist_track_img = Image.open(r'images\5_6p fascist track.png')
        elif len(self.game.players) in (7,8):
            self.fascist_track_img = Image.open(r'images\7_8p fascist track.png')
        elif len(self.game.players) in (9,10):
            self.fascist_track_img = Image.open(r'images\9_10p fascist track.png')
    
    def add_fascist_tile(self):
        """Adds a Fascist policy tile to the Fascist track."""
        pass

    def add_liberal_tile(self):
        """Adds a Liberal policy tile to the Liberal track."""
        pass

    def draw_election_tracker_token(self, position: int):
        """Draws the election tracker token at position."""
        
        token = ImageDraw.Draw(self.liberal_track_img)
        xy = GameBoard.ELEC_TRACKER_POS[position]
        token.ellipse(xy=xy,fill='#172f83')
        self.liberal_track_img.save(f"{self.game.game_id} lib track.png")
        

a = GameBoard(9)

