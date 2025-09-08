from __future__ import annotations

from dataclasses import asdict
from typing import List

from flask import Flask, jsonify, render_template, session

from blackjack import hand_value, should_dealer_draw
from deck_api import Card, DeckClient

app = Flask(__name__)
app.secret_key = "dev-key"  # for demonstration

# store deck clients in memory, keyed by deck id
DECKS: dict[str, DeckClient] = {}

BET_AMOUNT = 10
START_BANKROLL = 100


def _get_deck() -> DeckClient:
    deck_id = session.get("deck_id")
    if deck_id and deck_id in DECKS:
        return DECKS[deck_id]
    deck = DeckClient()
    DECKS[deck.deck_id] = deck
    session["deck_id"] = deck.deck_id
    return deck


def _cards_from_session(key: str) -> List[Card]:
    return [Card(**c) for c in session.get(key, [])]


def _save_cards(key: str, cards: List[Card]) -> None:
    session[key] = [asdict(c) for c in cards]


def _current_state(*, hide_dealer: bool, message: str = ""):
    player_cards = _cards_from_session("player_hand")
    dealer_cards = _cards_from_session("dealer_hand")

    p_total, _ = hand_value(player_cards) if player_cards else (0, False)
    if hide_dealer and dealer_cards:
        visible_dealer = [dealer_cards[0]]
        d_total = None
    else:
        visible_dealer = dealer_cards
        d_total, _ = hand_value(dealer_cards) if dealer_cards else (0, False)

    status = "player_turn" if session.get("in_round") else "waiting"
    return {
        "player": {"cards": [asdict(c) for c in player_cards], "value": p_total},
        "dealer": {
            "cards": [asdict(c) for c in visible_dealer],
            "value": d_total,
        },
        "bankroll": session.get("bankroll", START_BANKROLL),
        "status": status,
        "message": message,
    }


@app.route("/")
def index():
    # ensure bankroll exists
    session.setdefault("bankroll", START_BANKROLL)
    return render_template("index.html")


@app.route("/state")
def state():
    hide = session.get("in_round", False)
    return jsonify(_current_state(hide_dealer=hide))


@app.route("/start", methods=["POST"])
def start_round():
    deck = _get_deck()
    if deck.remaining < 0.25 * deck.initial_remaining:
        deck.reshuffle_remaining()

    player = deck.draw(2)
    dealer = deck.draw(2)
    _save_cards("player_hand", player)
    _save_cards("dealer_hand", dealer)
    session["in_round"] = True

    return jsonify(_current_state(hide_dealer=True))


@app.route("/hit", methods=["POST"])
def hit():
    if not session.get("in_round"):
        return jsonify(_current_state(hide_dealer=False))
    deck = _get_deck()
    player_cards = _cards_from_session("player_hand")
    player_cards.extend(deck.draw(1))
    _save_cards("player_hand", player_cards)
    total, _ = hand_value(player_cards)
    if total > 21:
        session["bankroll"] = session.get("bankroll", START_BANKROLL) - BET_AMOUNT
        session["in_round"] = False
        return jsonify(_current_state(hide_dealer=False, message="Bust! You lose."))
    return jsonify(_current_state(hide_dealer=True))


@app.route("/stand", methods=["POST"])
def stand():
    if not session.get("in_round"):
        return jsonify(_current_state(hide_dealer=False))
    deck = _get_deck()
    dealer_cards = _cards_from_session("dealer_hand")
    while should_dealer_draw(dealer_cards):
        dealer_cards.extend(deck.draw(1))
    _save_cards("dealer_hand", dealer_cards)

    player_total, _ = hand_value(_cards_from_session("player_hand"))
    dealer_total, _ = hand_value(dealer_cards)

    bankroll = session.get("bankroll", START_BANKROLL)
    if dealer_total > 21 or player_total > dealer_total:
        bankroll += BET_AMOUNT
        message = "You win!"
    elif player_total < dealer_total:
        bankroll -= BET_AMOUNT
        message = "Dealer wins!"
    else:
        message = "Push!"
    session["bankroll"] = bankroll
    session["in_round"] = False
    return jsonify(_current_state(hide_dealer=False, message=message))


if __name__ == "__main__":
    app.run(debug=True)
