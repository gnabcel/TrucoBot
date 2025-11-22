import unittest
from card import Card
from envido import calculate_envido_points

class TestTruco(unittest.TestCase):
    def test_card_values(self):
        c1 = Card(1, Card.ESPADA)
        c2 = Card(1, Card.BASTO)
        self.assertTrue(c1.get_truco_value() > c2.get_truco_value())
        
        c3 = Card(7, Card.ESPADA)
        c4 = Card(7, Card.ORO)
        self.assertTrue(c3.get_truco_value() > c4.get_truco_value())

    def test_envido_calculation(self):
        # 7 and 6 of same suit = 33
        hand1 = [Card(7, Card.ESPADA), Card(6, Card.ESPADA), Card(1, Card.BASTO)]
        self.assertEqual(calculate_envido_points(hand1), 33)
        
        # 7, 5, 4 of same suit = 20 + 7 + 5 = 32 (top 2)
        hand2 = [Card(7, Card.ORO), Card(5, Card.ORO), Card(4, Card.ORO)]
        self.assertEqual(calculate_envido_points(hand2), 32)
        
        # No matching suits, highest is 7
        hand3 = [Card(7, Card.ESPADA), Card(1, Card.BASTO), Card(1, Card.ORO)]
        self.assertEqual(calculate_envido_points(hand3), 7)

if __name__ == '__main__':
    unittest.main()
