import random

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score = 0
        self.played_cards = []

    def receive_cards(self, cards):
        self.hand = cards
        self.played_cards = []

    def play_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            card = self.hand.pop(card_index)
            self.played_cards.append(card)
            return card
        return None

class APIPlayer(Player):
    # API Player doesn't make automatic decisions, it waits for inputs from the Web UI.
    pass

class HeuristicBot(Player):
    def get_action(self, game_state):
        # Determine valid actions from game state
        valid_actions = game_state.get('valid_actions', [])
        
        # Helper rules
        envido_points = game_state.get('my_envido', 0)
        
        # 1. Answer Envido
        if 'envido_quiero' in valid_actions:
            if envido_points >= 26:
                return 'envido_quiero'
            else:
                return 'envido_no_quiero'
                
        # 2. Call Envido?
        if 'call_envido' in valid_actions and envido_points >= 28:
            return 'call_envido'
            
        # 3. Answer or call Truco/Retruco/Vale 4
        if 'truco_quiero' in valid_actions:
            # We must respond to a truco call.
            has_high_card = any(c.get_truco_value() >= 10 for c in self.hand)
            if has_high_card or random.random() < 0.3:
                return 'truco_quiero'
            return 'truco_no_quiero'
            
        if 'call_retruco' in valid_actions and random.random() < 0.2:
            return 'call_retruco'
        if 'call_vale_4' in valid_actions and random.random() < 0.1:
            return 'call_vale_4'

        # 4. Play Card
        card_actions = [a for a in valid_actions if a.startswith('play_card_')]
        if card_actions:
            # Play highest card if we are losing the round or it's the first round
            # Just simple for now: play largest card
            best_idx = 0
            best_val = -1
            for i, c in enumerate(self.hand):
                if c.get_truco_value() > best_val:
                    best_val = c.get_truco_value()
                    best_idx = i
            # Or mix it up
            if random.random() < 0.2:
                best_idx = random.randint(0, len(self.hand)-1)
                
            return f'play_card_{best_idx}'
            
        # Fallback random action
        if valid_actions:
            return random.choice(valid_actions)
        return None
