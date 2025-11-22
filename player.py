from abc import ABC, abstractmethod
import random

class Player(ABC):
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0

    def receive_cards(self, cards):
        self.hand = cards

    @abstractmethod
    def play_card(self, played_cards_in_round):
        pass

    @abstractmethod
    def call_envido(self, game_score_self, game_score_opponent):
        pass
    
    @abstractmethod
    def call_truco(self, game_score_self, game_score_opponent):
        pass

class RandomBot(Player):
    def play_card(self, played_cards_in_round):
        if not self.hand:
            return None
        # Simple random choice for now
        card_index = random.randint(0, len(self.hand) - 1)
        return self.hand.pop(card_index)

    def call_envido(self, game_score_self, game_score_opponent):
        # Randomly call envido 10% of the time if not already called
        return random.random() < 0.1

    def call_truco(self, game_score_self, game_score_opponent):
        # Randomly call truco 10% of the time
        return random.random() < 0.1

class HumanPlayer(Player):
    def play_card(self, played_cards_in_round):
        print(f"\n{self.name}'s hand:")
        for i, card in enumerate(self.hand):
            print(f"{i}: {card}")
        
        while True:
            try:
                choice = int(input("Choose a card to play (index): "))
                if 0 <= choice < len(self.hand):
                    return self.hand.pop(choice)
                else:
                    print("Invalid index.")
            except ValueError:
                print("Please enter a number.")

    def call_envido(self, game_score_self, game_score_opponent):
        choice = input("Call Envido? (y/n): ").lower()
        return choice == 'y'

    def call_truco(self, game_score_self, game_score_opponent):
        choice = input("Call Truco? (y/n): ").lower()
        return choice == 'y'
