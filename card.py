class Card:
    ESPADA = 'Espada'
    BASTO = 'Basto'
    ORO = 'Oro'
    COPA = 'Copa'
    
    SUITS = [ESPADA, BASTO, ORO, COPA]

    def __init__(self, rank, suit):
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank} de {self.suit}"

    def __str__(self):
        return f"{self.rank} de {self.suit}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def get_truco_value(self):
        # Hierarchy from highest to lowest
        # 1 Espada > 1 Basto > 7 Espada > 7 Oro > 3s > 2s > 1s (Cup/Gold) > 12s > 11s > 10s > 7s (Cup/Basto) > 6s > 5s > 4s
        
        if self.rank == 1 and self.suit == self.ESPADA: return 14
        if self.rank == 1 and self.suit == self.BASTO: return 13
        if self.rank == 7 and self.suit == self.ESPADA: return 12
        if self.rank == 7 and self.suit == self.ORO: return 11
        
        if self.rank == 3: return 10
        if self.rank == 2: return 9
        
        if self.rank == 1: return 8 # 1 Copa / 1 Oro
        
        if self.rank == 12: return 7
        if self.rank == 11: return 6
        if self.rank == 10: return 5
        
        if self.rank == 7: return 4 # 7 Copa / 7 Basto
        
        if self.rank == 6: return 3
        if self.rank == 5: return 2
        if self.rank == 4: return 1
        
        return 0

    def get_envido_value(self):
        if self.rank >= 10:
            return 0
        return self.rank
