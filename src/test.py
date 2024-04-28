from Classes.game import Game, GameBoard

game = Game('test2112','Justin',2112)
game.add_player(1,'Tom')
game.add_player(2,'Tom')
game.add_player(3,'Tom')
game.add_player(4,'Tom')
game.add_player(5,'Tom')
game.add_player(6,"Sean")

board = GameBoard(game)

for i in range(1,6):
    board.add_liberal_tile(i)
    game.liberal_policies_enacted += 1
board.liberal_track_img.show()
board.reset_election_tracker()
board.liberal_track_img.show()

