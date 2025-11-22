import random
from card import Card

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        self.cards = []
        ranks = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        for suit in Card.SUITS:
            for rank in ranks:
                self.cards.append(Card(rank, suit))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards in deck")
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt
