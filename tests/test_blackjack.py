import blackjack
from blackjack import hand_value, Player
from deck_api import Card, DeckClient


def _card(code: str, value: str) -> Card:
    return Card(code=code, value=value, suit="TEST", image="")


def test_hand_value_cases():
    total, soft = hand_value([_card("AH", "ACE"), _card("6D", "6")])
    assert total == 17 and soft

    total, soft = hand_value([_card("AH", "ACE"), _card("AD", "ACE"), _card("9C", "9")])
    assert total == 21 and not soft

    total, soft = hand_value([
        _card("AH", "ACE"),
        _card("AD", "ACE"),
        _card("9C", "9"),
        _card("KH", "KING"),
    ])
    assert total == 21 and not soft

    total, soft = hand_value([_card("AH", "ACE"), _card("9C", "9"), _card("KH", "KING")])
    assert total == 20 and not soft


def test_play_round_smoke(monkeypatch):
    def fake_init(self, decks: int = 6, session=None) -> None:
        self.deck_id = "test"
        self.initial_remaining = 52 * decks
        self._remaining = self.initial_remaining

    monkeypatch.setattr(DeckClient, "__init__", fake_init)

    sequence = [
        [_card("10H", "10"), _card("9C", "9")],  # player
        [_card("7D", "7"), _card("8S", "8")],   # dealer
        [_card("QC", "QUEEN")],                    # dealer draw (busts)
    ]

    def fake_draw(self, n: int = 1):
        self._remaining -= n
        return sequence.pop(0)

    monkeypatch.setattr(DeckClient, "draw", fake_draw)
    monkeypatch.setattr(DeckClient, "reshuffle_remaining", lambda self: None)
    monkeypatch.setattr(blackjack, "prompt_hit_or_stand", lambda: "stand")

    client = DeckClient()
    player = Player("Tester", bankroll=100, bet=10)
    stats = {"played": 0, "won": 0, "lost": 0, "push": 0}

    blackjack.play_round(client, player, stats)

    assert player.bankroll == 110
    assert stats == {"played": 1, "won": 1, "lost": 0, "push": 0}
