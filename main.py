from game import TrucoGame
from player import HumanPlayer, RandomBot

if __name__ == "__main__":
    print("Welcome to TrucoBot!")
    name = input("Enter your name: ")
    human = HumanPlayer(name)
    bot = RandomBot("Bot")
    
    game = TrucoGame(human, bot)
    game.play()
