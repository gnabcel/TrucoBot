from deck import Deck
from envido import calculate_envido_points

class TrucoGame:
    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.deck = Deck()
        self.p1_score = 0
        self.p2_score = 0
        self.target_score = 30

    def play(self):
        print(f"Starting game: {self.p1.name} vs {self.p2.name}")
        round_num = 1
        while self.p1_score < self.target_score and self.p2_score < self.target_score:
            print(f"\n--- Round {round_num} ---")
            print(f"Score: {self.p1.name}: {self.p1_score} | {self.p2.name}: {self.p2_score}")
            self.play_hand()
            round_num += 1
        
        winner = self.p1 if self.p1_score >= self.target_score else self.p2
        print(f"\nGame Over! Winner: {winner.name}")

    def play_hand(self):
        self.deck.reset()
        self.p1.receive_cards(self.deck.deal(3))
        self.p2.receive_cards(self.deck.deal(3))

        # Envido phase (simplified: auto-calculate for now to show mechanics)
        p1_envido = calculate_envido_points(self.p1.hand)
        p2_envido = calculate_envido_points(self.p2.hand)
        
        # In a real game, players would bid. Here we just compare.
        # print(f"Envido: {self.p1.name} ({p1_envido}) vs {self.p2.name} ({p2_envido})")
        
        # Truco rounds (best of 3)
        p1_rounds = 0
        p2_rounds = 0
        
        # Who starts? Alternating would be better, but fixed for now
        current_player = self.p1
        other_player = self.p2
        
        for i in range(3):
            if p1_rounds == 2 or p2_rounds == 2:
                break
                
            print(f"\nHand Round {i+1}")
            
            # P1 plays
            c1 = self.p1.play_card([])
            print(f"{self.p1.name} plays {c1}")
            
            # P2 plays
            c2 = self.p2.play_card([c1])
            print(f"{self.p2.name} plays {c2}")
            
            # Evaluate winner of this hand round
            val1 = c1.get_truco_value()
            val2 = c2.get_truco_value()
            
            if val1 > val2:
                print(f"{self.p1.name} wins this hand round")
                p1_rounds += 1
            elif val2 > val1:
                print(f"{self.p2.name} wins this hand round")
                p2_rounds += 1
            else:
                print("Tie (Parda)")
                # Parda rules are complex, simplified: first to win next wins all, or if first round parda, second round winner wins.
                # For this basic engine, let's give point to P1 (hand) - TODO: fix parda logic
                p1_rounds += 1 
        
        if p1_rounds > p2_rounds:
            self.p1_score += 1
            print(f"{self.p1.name} wins the round (1 point)")
        else:
            self.p2_score += 1
            print(f"{self.p2.name} wins the round (1 point)")
