def calculate_envido_points(cards):
    if len(cards) != 3:
        raise ValueError("Envido requires exactly 3 cards")

    # Group by suit
    suits = {}
    for card in cards:
        if card.suit not in suits:
            suits[card.suit] = []
        suits[card.suit].append(card)

    max_score = 0

    # Check for Flor (3 cards of same suit) - simplified for now, usually Flor is a separate call
    # But standard Envido rules say if you have 2 cards of same suit, you add 20 + their values.
    
    # Find suit with most cards
    best_suit = None
    max_count = 0
    for suit, suit_cards in suits.items():
        if len(suit_cards) > max_count:
            max_count = len(suit_cards)
            best_suit = suit
    
    if max_count >= 2:
        # Calculate score for the 2 highest cards of that suit
        suit_cards = sorted(suits[best_suit], key=lambda c: c.get_envido_value(), reverse=True)
        # Take top 2
        c1 = suit_cards[0]
        c2 = suit_cards[1]
        score = 20 + c1.get_envido_value() + c2.get_envido_value()
        if score > max_score:
            max_score = score
    
    # Also check individual cards (if no 2 cards of same suit, or if individual card is somehow better - rare but possible if 0 matches)
    # Actually, if no matches, it's just the highest single card
    for card in cards:
        if card.get_envido_value() > max_score:
            max_score = card.get_envido_value()
            
    return max_score