from Game import Game

game = Game()

players = int(input("Скільки гравців? "))
game.create_cards(players)
game.show_game()