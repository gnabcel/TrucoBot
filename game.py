from deck import Deck
from envido import calculate_envido_points, EnvidoState, EnvidoResponse, get_quiero_points, get_no_quiero_points
from truco import TrucoState, get_truco_points, get_next_truco_state

import random

class GamePhase:
    DEALING = "dealing"
    PLAYING = "playing"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"

class TrucoGame:
    def __init__(self, p1, p2, target_score=30):
        self.p1 = p1
        self.p2 = p2
        self.deck = Deck()
        self.p1_score = 0
        self.p2_score = 0
        self.target_score = target_score
        self.hand_number = 0
        self.log = []
        
        self.reset_round()
        
    def add_log(self, msg):
        self.log.append(msg)
        
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
        self.envido_played = False
        self.envido_points_p1 = 0
        self.envido_points_p2 = 0
        self.envido_winner = None
        
        self.truco_state = TrucoState.NOT_CALLED
        self.truco_owner = None # Who called it last (other person must accept/raise)
        self.truco_turn = None # Who can RAISE the truco
        
        self.waiting_for_response = None # 'envido' or 'truco'
        self.cards_played_this_turn = []
        
        self.add_log(f"--- Arranca la Mano {self.hand_number + 1} ---")
        self.add_log(f"Reparte: {'Vos' if self.current_turn != self.p1 else 'TrucoBot'}")
        
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
            "waiting_for_response": self.waiting_for_response,
            "log": self.log,
            "truco_turn": 1 if self.truco_turn == self.p1 else (2 if self.truco_turn == self.p2 else None)
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
        # Fix: envido_played tracking stops multiple envido calls if it already passed.
        if len(self.round_winners) == 0 and not has_played and self.envido_state == EnvidoState.NOT_CALLED and not self.envido_played and self.truco_state == TrucoState.NOT_CALLED:
            actions.extend(['call_envido', 'call_real_envido', 'call_falta_envido'])
            
        # Call Truco (Sequence: Nada -> Truco -> Retruco -> Vale 4)
        if self.truco_state == TrucoState.NOT_CALLED:
            actions.append('call_truco')
        elif self.truco_turn == player:
            next_state = get_next_truco_state(self.truco_state)
            if next_state:
                actions.append(f'call_{next_state}')
                
        # Make sure that playing a card is ONLY allowed if 'truco' isn't waiting
        if self.waiting_for_response == 'truco':
            actions = [a for a in actions if not a.startswith('play_card_')]
                
        return actions

    def handle_action(self, player, action):
        if player != self.current_turn:
            return False, "Not your turn"
            
        if action not in self.get_valid_actions(player):
            return False, f"Invalid action {action}"

        name = "Vos" if player == self.p1 else "TrucoBot"

        # Flavor text helpers
        quiero_envido_phrases = ["¡Quiero!", "¡Se la rre banca, quiero!", "¡Quiero y retruco no... mentira, quiero!", "Venga ese envido."]
        no_quiero_envido_phrases = ["No quiero.", "Paso.", "Son buenas, me achico.", "No me da el cuero, no quiero."]
        quiero_truco_phrases = ["¡Quiero!", "¡Vení que me la banco!", "A ver si sos tan guapo, ¡quiero!", "Dale, quiero."]
        no_quiero_truco_phrases = ["Me voy al mazo.", "Te la dejo.", "No tengo nada, me chicho.", "Buen truco, me achico."]
        
        # Determine specific phrase for Bot vs Player
        def get_phrase(phrases_list, is_bot):
            return random.choice(phrases_list) if is_bot else phrases_list[0]

        is_bot = player == self.p2

        # Handle Responses
        if action == 'envido_quiero':
            phrase = get_phrase(quiero_envido_phrases, is_bot)
            self.add_log(f"{name}: {phrase}")
            self.resolve_envido(accepted=True)
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player) # Return turn to whoever called it (simplified)
            # Actually turn returns to whoever has to play a card
            # To be accurate, turn returns to whoever's turn it was before the calls started
            return True, "Envido accepted"
            
        elif action == 'envido_no_quiero':
            phrase = get_phrase(no_quiero_envido_phrases, is_bot)
            self.add_log(f"{name}: {phrase}")
            self.resolve_envido(accepted=False)
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player)
            return True, "Envido rejected"
            
        elif action.startswith('truco_quiero'):
            phrase = get_phrase(quiero_truco_phrases, is_bot)
            next_state = get_next_truco_state(self.truco_state)
            
            self.add_log(f"{name}: {phrase}")
            if next_state == TrucoState.VALE_4 and self.truco_state == TrucoState.RETRUCO:
                 self.truco_state = TrucoState.VALE_4 # accepted vale 4
                 self.truco_turn = None # nobody can raise anymore
            elif self.truco_state == TrucoState.RETRUCO:
                 # It was recently raised TO retruco, so we are accepting retruco
                 # The 'truco_state' is already RETRUCO from the call. 
                 # We just confirm it.
                 pass
            elif self.truco_state == TrucoState.TRUCO:
                 pass
                 
            self.truco_turn = self.get_opponent(player) # The one who didn't accept gets the turn to raise
            self.waiting_for_response = None
            self.current_turn = self.get_opponent(player)
            return True, "Truco accepted"
            
        elif action == 'truco_no_quiero':
            phrase = get_phrase(no_quiero_truco_phrases, is_bot)
            self.add_log(f"{name}: {phrase}")
            self.resolve_truco_rejection(player)
            return True, "Truco rejected"

        # Handle Calls
        if action.startswith('call_'):
            call_type = action[len('call_'):]
            call_names = {
                'envido': '¡Envido!', 'real_envido': '¡Real Envido!', 'falta_envido': '¡Falta Envido carajo!',
                'truco': '¡Truco!', 'retruco': '¡Quiero Retruco!', 'vale_4': '¡Quiero Vale Cuatro!'
            }
            cname = call_names.get(call_type, call_type)
            # Flavor variation for bot
            if is_bot and call_type == 'truco':
                cname = random.choice(["¡Truco!", "Jugá que te canto Truco.", "Te veo flojo... ¡Truco!"])
            elif is_bot and call_type == 'envido':
                cname = random.choice(["¡Envido!", "Tengo puntitos... ¡Envido!", "Canto Envido."])
                
            self.add_log(f"{name}: {cname}")
            
            if call_type in ['envido', 'real_envido', 'falta_envido']:
                self.envido_state = call_type
                self.envido_history.append(call_type)
                self.envido_played = True
                self.waiting_for_response = 'envido'
                self.current_turn = self.get_opponent(player)
                return True, f"Called {call_type}"
            elif call_type in ['truco', 'retruco', 'vale_4']:
                self.truco_state = call_type # state becomes the call immediately
                self.truco_owner = player # only owner can be rejected
                self.truco_turn = None # nobody can raise while waiting
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
                
            self.add_log(f"{name} juega: {card}")
                
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
            
            self.add_log(f"Puntos de Envido: Vos ({self.envido_points_p1}) vs TrucoBot ({self.envido_points_p2})")
            
            if self.envido_points_p1 > self.envido_points_p2:
                self.p1_score += pts
                self.envido_winner = self.p1
                self.add_log(f"Vos ganás {pts} puntos de Envido.")
            elif self.envido_points_p2 > self.envido_points_p1:
                self.p2_score += pts
                self.envido_winner = self.p2
                self.add_log(f"TrucoBot gana {pts} puntos de Envido.")
            else:
                if is_p1_mano:
                    self.p1_score += pts
                    self.envido_winner = self.p1
                    self.add_log(f"Empate. Vos sos mano y ganás {pts} puntos.")
                else:
                    self.p2_score += pts
                    self.envido_winner = self.p2
                    self.add_log(f"Empate. TrucoBot es mano y gana {pts} puntos.")
        else:
            # simple for now
            pts = get_no_quiero_points(self.envido_state)
            opp = self.get_opponent(self.current_turn)
            if opp == self.p1:
                self.p1_score += pts
                self.add_log(f"Vos ganás {pts} puntos porque TrucoBot no quiso.")
            else:
                self.p2_score += pts
                self.add_log(f"TrucoBot gana {pts} puntos porque no quisiste.")
                
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
            self.add_log("-> Vos ganás la baza.")
        elif trick_winner == self.p2:
            winner_id = 2
            self.add_log("-> TrucoBot gana la baza.")
        else:
            self.add_log("-> ¡Parda! (Empate)")
            
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
                self.add_log(f"¡Vos ganás la mano! Sumás {pts} puntos.")
                self.p1_score += pts
            else:
                self.add_log(f"TrucoBot gana la mano. Suma {pts} puntos.")
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
            if self.p1_score >= self.target_score:
                self.add_log("¡Ganaste la partida!")
            else:
                self.add_log("TrucoBot ganó la partida.")
            return True
        return False
