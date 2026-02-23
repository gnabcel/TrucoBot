class EnvidoState:
    NOT_CALLED = "not_called"
    ENVIDO = "envido"
    REAL_ENVIDO = "real_envido"
    FALTA_ENVIDO = "falta_envido"
    ENVIDO_ENVIDO = "envido_envido"
    ENVIDO_REAL_ENVIDO = "envido_real_envido"
    ENVIDO_ENVIDO_REAL_ENVIDO = "envido_envido_real_envido"

class EnvidoResponse:
    QUIERO = "quiero"
    NO_QUIERO = "no_quiero"

# Mapping of valid responses to a given envido state
# returns new state if increasing bet, or final points if Quiero/No_Quiero
def get_envido_options(current_state):
    if current_state == EnvidoState.NOT_CALLED:
        return [EnvidoState.ENVIDO, EnvidoState.REAL_ENVIDO, EnvidoState.FALTA_ENVIDO]
    elif current_state == EnvidoState.ENVIDO:
        return [EnvidoState.ENVIDO_ENVIDO, EnvidoState.REAL_ENVIDO, EnvidoState.FALTA_ENVIDO, EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    elif current_state == EnvidoState.ENVIDO_ENVIDO:
        return [EnvidoState.ENVIDO_REAL_ENVIDO, EnvidoState.FALTA_ENVIDO, EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    elif current_state == EnvidoState.REAL_ENVIDO:
        return [EnvidoState.FALTA_ENVIDO, EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    elif current_state == EnvidoState.ENVIDO_REAL_ENVIDO:
        return [EnvidoState.FALTA_ENVIDO, EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    elif current_state == EnvidoState.ENVIDO_ENVIDO_REAL_ENVIDO:
        return [EnvidoState.FALTA_ENVIDO, EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    elif current_state == EnvidoState.FALTA_ENVIDO:
        return [EnvidoResponse.QUIERO, EnvidoResponse.NO_QUIERO]
    return []

# Points evaluation when accepted (Quiero)
def get_quiero_points(state, current_score_leader, target_score):
    points = {
        EnvidoState.ENVIDO: 2,
        EnvidoState.ENVIDO_ENVIDO: 4,
        EnvidoState.REAL_ENVIDO: 3,
        EnvidoState.ENVIDO_REAL_ENVIDO: 5,
        EnvidoState.ENVIDO_ENVIDO_REAL_ENVIDO: 7,
    }
    if state == EnvidoState.FALTA_ENVIDO:
        return target_score - current_score_leader
    return points.get(state, 2)

# Points evaluation when rejected (No Quiero)
def get_no_quiero_points(state):
    points = {
        EnvidoState.ENVIDO: 1,
        EnvidoState.ENVIDO_ENVIDO: 2,
        EnvidoState.REAL_ENVIDO: 1,
        EnvidoState.ENVIDO_REAL_ENVIDO: 2,
        EnvidoState.ENVIDO_ENVIDO_REAL_ENVIDO: 4,
        EnvidoState.FALTA_ENVIDO: 1 # In Falta Envido, default reject base is 1, but complex if chained. Simplified here.
    }
    
    # Specific logic for rejection of Falta Envido when there are previous bets
    if state == EnvidoState.FALTA_ENVIDO:
        # We need the previous state... this requires tracking history, but simplified: reject Falta Envido is 1. If it came after Envido it's 2, etc.
        # This will be handled in game logic state machine by tracking accumulated points.
        pass
        
    return points.get(state, 1)

def get_reject_points(history):
    # History contains the sequence of calls
    if not history: return 0
    if len(history) == 1: return 1 # No quiero al primero
    
    # Sum points up to the previous bet
    # If history is [Envido, Real Envido] -> Player 2 rejects Real Envido -> Player 1 wins the previous Envido (2 points)
    # This is a bit complex, simplest rule: 
    # If someone rejects real envido, they pay the value of the previous calls.
    # Reject 1st call = 1
    # Reject anything else = value of previous call. 
    prev_state = history[-2]
    return get_quiero_points(prev_state, 0, 30) # For history we just need the non-falta points

def calculate_envido_points(cards):
    if len(cards) != 3:
        raise ValueError("Envido requires exactly 3 cards")

    suits = {}
    for card in cards:
        if card.suit not in suits:
            suits[card.suit] = []
        suits[card.suit].append(card)

    max_score = 0
    
    best_suit = None
    max_count = 0
    for suit, suit_cards in suits.items():
        if len(suit_cards) > max_count:
            max_count = len(suit_cards)
            best_suit = suit
    
    if max_count >= 2:
        suit_cards = sorted(suits[best_suit], key=lambda c: c.get_envido_value(), reverse=True)
        c1 = suit_cards[0]
        c2 = suit_cards[1]
        score = 20 + c1.get_envido_value() + c2.get_envido_value()
        if score > max_score:
            max_score = score
            
    for card in cards:
        if card.get_envido_value() > max_score:
            max_score = card.get_envido_value()
            
    return max_score