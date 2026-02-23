from deck import Deck
from envido import calculate_envido_points, EnvidoState, EnvidoResponse, get_quiero_points, get_no_quiero_points
from truco import TrucoState, get_truco_points, get_next_truco_state

class GamePhase:
    DEALING = "dealing"
    PLAYING = "playing"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"

class TrucoGame:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.deck = Deck()
        self.p1_score = 0
        self.p2_score = 0
        self.target_score = 30
        self.hand_number = 0
        
        self.reset_round()
        
    def reset_round(self):
        self.phase = GamePhase.DEALING
        self.current_turn = self.p1 if self.hand_number % 2 == 0 else self.p2
        self.hand_winner = None
        self.deck.reset()
        
        # Round state
        self.played_cards_p1 = []
        self.played_cards_p2 = []
        self.round_winners = [] # 1 for p1, 2 for p2, 0 for parda
        
        self.envido_state = EnvidoState.NOT_CALLED
        self.envido_history = []
        self.envido_points_p1 = 0
        self.envido_points_p2 = 0
        self.envido_winner = None
        
        self.truco_state = TrucoState.NOT_CALLED
        self.truco_owner = None # Who called it last (other person must accept/raise)
        
        self.waiting_for_response = None # 'envido' or 'truco'
        self.cards_played_this_turn = []
        
        self.deal()
        
    def deal(self):
        self.p1.receive_cards(self.deck.deal(3))
        self.p2.receive_cards(self.deck.deal(3))
        self.envido_points_p1 = calculate_envido_points(self.p1.hand)
        self.envido_points_p2 = calculate_envido_points(self.p2.hand)
        self.phase = GamePhase.PLAYING
        
    def get_opponent(self, player):
        return self.p2 if player == self.p1 else self.p1
        
    def get_state_for_player(self, player):
        opp = self.get_opponent(player)
        
        is_turn = (self.current_turn == player)
        valid_actions = self.get_valid_actions(player) if is_turn else []
        
        return {
            "phase": self.phase,
            "my_score": self.p1_score if player == self.p1 else self.p2_score,
            "opp_score": self.p2_score if player == self.p1 else self.p1_score,
            "my_cards": [{"id": i, "str": str(c)} for i, c in enumerate(player.hand)],
            "my_played": [str(c) for c in (self.played_cards_p1 if player == self.p1 else self.played_cards_p2)],
            "opp_played": [str(c) for c in (self.played_cards_p2 if player == self.p1 else self.played_cards_p1)],
            "cards_on_table": [str(c) for c in self.cards_played_this_turn],
            "is_turn": is_turn,
            "valid_actions": valid_actions,
            "envido_state": self.envido_state,
            "truco_state": self.truco_state,
            "my_envido": self.envido_points_p1 if player == self.p1 else self.envido_points_p2,
            "hand_number": self.hand_number,
            "round_winners": self.round_winners,
            "waiting_for_response": self.waiting_for_response
        }
        
    def get_valid_actions(self, player):
        if self.phase != GamePhase.PLAYING:
            return []
            
        actions = []
        
        if self.waiting_for_response == 'envido':
            actions.extend(['envido_quiero', 'envido_no_quiero'])
            # Can also raise
            if self.envido_state == EnvidoState.ENVIDO:
                actions.extend(['call_envido', 'call_real_envido', 'call_falta_envido'])
            elif self.envido_state in [EnvidoState.REAL_ENVIDO, EnvidoState.ENVIDO_ENVIDO]:
                actions.extend(['call_falta_envido'])
            return actions
            
        if self.waiting_for_response == 'truco':
            actions.extend(['truco_quiero', 'truco_no_quiero'])
            # Can raise if state allows
            next_state = get_next_truco_state(self.truco_state)
            if next_state:
                actions.append(f'call_{next_state}')
            return actions
            
        # Normal play
        for i in range(len(player.hand)):
            actions.append(f"play_card_{i}")
            
        # Call Envido (only if first round and no cards played by this player)
        has_played = (len(self.played_cards_p1) > 0 if player == self.p1 else len(self.played_cards_p2) > 0)
        if len(self.round_winners) == 0 and not has_played and self.envido_state == EnvidoState.NOT_CALLED:
            actions.extend(['call_envido', 'call_real_envido', 'call_falta_envido'])
            
        # Call Truco
        if self.truco_state == TrucoState.NOT_CALLED:
            actions.append('call_truco')
        elif self.truco_owner != player:
            next_state = get_next_truco_state(self.truco_state)
            if next_state:
                actions.append(f'call_{next_state}')
                
        return actions

    def handle_action(self, player, action):
        if player != self.current_turn:
            return False, "Not your turn"
            
        if action not in self.get_valid_actions(player):
            return False, f"Invalid action {action}"

        # Handle Responses
        if action == 'envido_quiero':
            self.resolve_envido(accepted=True)
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player) # Return turn to whoever called it (simplified)
            # Actually turn returns to whoever has to play a card
            # To be accurate, turn returns to whoever's turn it was before the calls started
            return True, "Envido accepted"
            
        elif action == 'envido_no_quiero':
            self.resolve_envido(accepted=False)
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player)
            return True, "Envido rejected"
            
        elif action == 'truco_quiero':
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player)
            return True, "Truco accepted"
            
        elif action == 'truco_no_quiero':
            self.resolve_truco_rejection(player)
            return True, "Truco rejected"

        # Handle Calls
        if action.startswith('call_'):
            call_type = action[len('call_'):]
            if call_type in ['envido', 'real_envido', 'falta_envido']:
                self.envido_state = call_type
                self.envido_history.append(call_type)
                self.waiting_for_response = 'envido'
                self.current_turn = self.get_opponent(player)
                return True, f"Called {call_type}"
            elif call_type in ['truco', 'retruco', 'vale_4']:
                self.truco_state = call_type
                self.truco_owner = player
                self.waiting_for_response = 'truco'
                self.current_turn = self.get_opponent(player)
                return True, f"Called {call_type}"

        # Handle Play Card
        if action.startswith('play_card_'):
            idx = int(action.split('_')[2])
            card = player.play_card(idx)
            self.cards_played_this_turn.append(card)
            
            if player == self.p1:
                self.played_cards_p1.append(card)
            else:
                self.played_cards_p2.append(card)
                
            # If both have played, resolve the trick
            if len(self.cards_played_this_turn) == 2:
                self.resolve_trick()
            else:
                self.current_turn = self.get_opponent(player)
                
            return True, f"Played {card}"
            
        return False, "Unknown action"

    def resolve_envido(self, accepted):
        if accepted:
            leader_score = max(self.p1_score, self.p2_score)
            pts = get_quiero_points(self.envido_state, leader_score, self.target_score)
            
            # evaluate who has more points
            # In tie, player who is "Mano" (P1 if hand_number is even) wins
            is_p1_mano = (self.hand_number % 2 == 0)
            
            if self.envido_points_p1 > self.envido_points_p2:
                self.p1_score += pts
                self.envido_winner = self.p1
            elif self.envido_points_p2 > self.envido_points_p1:
                self.p2_score += pts
                self.envido_winner = self.p2
            else:
                if is_p1_mano:
                    self.p1_score += pts
                    self.envido_winner = self.p1
                else:
                    self.p2_score += pts
                    self.envido_winner = self.p2
        else:
            # simple for now
            pts = get_no_quiero_points(self.envido_state)
            opp = self.get_opponent(self.current_turn)
            if opp == self.p1:
                self.p1_score += pts
            else:
                self.p2_score += pts
                
        self.check_game_over()

    def resolve_truco_rejection(self, rejecting_player):
        pts = 1
        if self.truco_state == TrucoState.RETRUCO: pts = 2
        elif self.truco_state == TrucoState.VALE_4: pts = 3
        
        opp = self.get_opponent(rejecting_player)
        if opp == self.p1:
            self.p1_score += pts
        else:
            self.p2_score += pts
            
        self.end_round()

    def resolve_trick(self):
        c1 = self.cards_played_this_turn[0]
        c2 = self.cards_played_this_turn[1]
        
        # c1 was played by the person who went first this trick
        # So we need to map c1 and c2 to p1 and p2 based on who played first
        first_player = self.get_opponent(self.current_turn)
        
        v1 = c1.get_truco_value()
        v2 = c2.get_truco_value()
        
        winner_id = 0 # 0=parda, 1=p1, 2=p2
        trick_winner = None
        
        if v1 > v2:
            trick_winner = first_player
        elif v2 > v1:
            trick_winner = self.current_turn
        else:
            winner_id = 0 # parda
            
        if trick_winner == self.p1:
            winner_id = 1
        elif trick_winner == self.p2:
            winner_id = 2
            
        self.round_winners.append(winner_id)
        self.cards_played_this_turn = []
        
        # Determine who starts next trick
        if winner_id != 0:
            self.current_turn = self.p1 if winner_id == 1 else self.p2
        else:
            # In parda, the one who is "mano" starts. First player of the hand.
            self.current_turn = self.p1 if self.hand_number % 2 == 0 else self.p2
            
        self.check_round_end()
        
    def check_round_end(self):
        # Determine if someone has won 2 tricks or if pardas dictate a win
        p1_wins = self.round_winners.count(1)
        p2_wins = self.round_winners.count(2)
        pardas = self.round_winners.count(0)
        
        round_over = False
        winner = None
        
        if p1_wins == 2:
            round_over = True; winner = self.p1
        elif p2_wins == 2:
            round_over = True; winner = self.p2
        elif len(self.round_winners) >= 2:
            # Complex parda logic
            if pardas == 1:
                # If they tied one, whoever won the other wins the round
                if p1_wins == 1: round_over = True; winner = self.p1
                if p2_wins == 1: round_over = True; winner = self.p2
            elif pardas >= 2:
                # If two pardas, mano wins (p1 if hand%2==0)
                round_over = True
                winner = self.p1 if self.hand_number % 2 == 0 else self.p2
        elif len(self.round_winners) == 3:
             # Should be covered above, but just in case
             if p1_wins > p2_wins: winner = self.p1
             else: winner = self.p2
             round_over = True
             
        if round_over:
            pts = get_truco_points(self.truco_state)
            if winner == self.p1:
                self.p1_score += pts
            else:
                self.p2_score += pts
            self.end_round()

    def end_round(self):
        self.phase = GamePhase.ROUND_END
        self.hand_number += 1
        if not self.check_game_over():
            self.reset_round()
            
    def check_game_over(self):
        if self.p1_score >= self.target_score or self.p2_score >= self.target_score:
            self.phase = GamePhase.GAME_OVER
            return True
        return False
