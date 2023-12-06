"""
This module manages all game board management operations.
"""

from PIL import Image, ImageDraw
from io import BytesIO
import discord
# from game import Game


class GameBoard:
    """Represents a Secret Hitler game board/track."""

    ELEC_TRACKER_POS = {
            1: (1447,1211,1591,1355),
            2: (1847,1211,1991,1355),
            3: (2252,1211,2396,1355),
            4: (2652,1211,2796,1355),
        }
    
    FASCIST_TILE_POS = fpos = {
            1: (410,400),
            2: (1010,400),
            3: (1610,400),
            4: (2210,400),
            5: (2810,400),
            6: (3410,400)
        }
    
    LIBERAL_TILE_POS = {
            1: (690,380),
            2: (1290,380),
            3: (1890,380),
            4: (2490,380),
            5: (3090,380)
        }
    
    FASCIST_TILE = r'images\fascist tile.png'
    LIBERAL_TILE = r'images\liberal tile.png'

    LIBERAL_TRACK = r'images\liberal track.png'
    FASCIST_TRACK_5_6 = r'images\5_6p fascist track.png'
    FASCIST_TRACK_7_8 = r'images\7_8p fascist track.png'
    FASCIST_TRACK_9_10 = r'images\9_10p fascist track.png'

    def __init__(self, game):
        self.game = game
        self.liberal_track_img = Image.open(GameBoard.LIBERAL_TRACK)
        self.draw_election_tracker_token(1)
        self.get_fascist_track()
        self.fascist_track_img.show()
        
    def get_fascist_track(self):

        if len(self.game.players) in (5,6):
            self.fascist_track_img = Image.open(GameBoard.FASCIST_TRACK_5_6)
        elif len(self.game.players) in (7,8):
            self.fascist_track_img = Image.open(GameBoard.FASCIST_TRACK_7_8)
        elif len(self.game.players) in (9,10):
            self.fascist_track_img = Image.open(GameBoard.FASCIST_TRACK_9_10)
        
        else:
            print("error, players not counted")
        
    def add_fascist_tile(self):
        """Adds a Fascist policy to the Fascist track and returns a Discord File
        containing the updated game board image."""
        
        tile = Image.open(GameBoard.FASCIST_TILE)
        slot = GameBoard.FASCIST_TILE_POS[self.game.fascist_policies_enacted + 1] 
        self.fascist_track_img.paste(tile,slot)
        self.fascist_track_img.show()

        return self.create_discord_file(self.fascist_track_img)

    def add_liberal_tile(self):
        """Adds a Liberal policy to the Liberal track and returns a Discord File
        containing the updated game board image."""
        
        tile = Image.open(GameBoard.LIBERAL_TILE)
        slot = GameBoard.LIBERAL_TILE_POS[self.game.liberal_policies_enacted + 1]
        self.liberal_track_img.paste(tile,slot)

        return self.create_discord_file(self.liberal_track_img)

    def draw_election_tracker_token(self, position: int):
        """Draws the election tracker token at position and returns a Discord
        File containing the updated game board image."""
        
        token = ImageDraw.Draw(self.liberal_track_img)
        xy = GameBoard.ELEC_TRACKER_POS[position]
        token.ellipse(xy=xy,fill='#172f83')

        return self.create_discord_file(self.liberal_track_img)
    
    def reset(self):
        """Resets the game board to starting state."""

        self.liberal_track_img = Image.open(GameBoard.LIBERAL_TRACK)
        self.draw_election_tracker_token(1)
        self.get_fascist_track()

    def create_discord_file(self, img: Image.Image):
        """Returns a Discord File object containing img."""

        image_bytesio = BytesIO()
        img.save(image_bytesio, format='PNG')
        image_bytesio.seek(0)

        return discord.File(image_bytesio,filename="image.png")