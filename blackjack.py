from __future__ import annotations

from dataclasses import dataclass, field
import argparse
from typing import List, Tuple

from deck_api import DeckClient, Card


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)

    def add(self, *cs: Card) -> None:
        self.cards.extend(cs)

    def as_codes(self) -> str:
        return ", ".join(c.code for c in self.cards)


@dataclass
class Player:
    name: str
    bankroll: int
    bet: int


def hand_value(cards: List[Card]) -> Tuple[int, bool]:
    """Return the Blackjack value for ``cards``.

    The total is calculated with standard Blackjack rules where face cards
    count as 10 and aces can count as 1 or 11.  The returned tuple contains
    the numeric total and a boolean indicating whether the hand is *soft*
    (i.e. at least one ace is counted as 11).
    """

    total = 0
    aces = 0
    for c in cards:
        v = c.value
        if v in {"JACK", "QUEEN", "KING"}:
            total += 10
        elif v == "ACE":
            total += 11
            aces += 1
        else:
            total += int(v)

    while total > 21 and aces:
        total -= 10
        aces -= 1

    is_soft = aces > 0 and total < 21
    return total, is_soft


def should_dealer_draw(cards: List[Card]) -> bool:
    """Return ``True`` if the dealer should draw another card.

    By default the dealer stands on all 17s, including soft 17.  The logic is
    therefore simply a check that the total is below 17.
    """

    total, _ = hand_value(cards)
    return total < 17


def prompt_hit_or_stand() -> str:
    while True:
        choice = input("Hit or stand? [h/s]: ").strip().lower()
        if choice in {"h", "hit"}:
            return "hit"
        if choice in {"s", "stand"}:
            return "stand"


def play_round(client: DeckClient, player: Player, stats: dict) -> None:
    if client.remaining < 0.25 * client.initial_remaining:
        client.reshuffle_remaining()

    player_hand = Hand()
    dealer_hand = Hand()
    player_hand.add(*client.draw(2))
    dealer_hand.add(*client.draw(2))

    p_total, _ = hand_value(player_hand.cards)
    print(f"Player: {player_hand.as_codes()} ({p_total})")
    print(f"Dealer: {dealer_hand.cards[0].code}, [hidden]")

    while True:
        decision = prompt_hit_or_stand()
        if decision == "hit":
            player_hand.add(*client.draw(1))
            p_total, _ = hand_value(player_hand.cards)
            print(f"Player: {player_hand.as_codes()} ({p_total})")
            if p_total > 21:
                print("Bust! You lose.")
                player.bankroll -= player.bet
                stats["lost"] += 1
                stats["played"] += 1
                return
        else:
            break

    d_total, _ = hand_value(dealer_hand.cards)
    print(f"Dealer: {dealer_hand.as_codes()} ({d_total})")
    while should_dealer_draw(dealer_hand.cards):
        dealer_hand.add(*client.draw(1))
        d_total, _ = hand_value(dealer_hand.cards)
        print(f"Dealer: {dealer_hand.as_codes()} ({d_total})")

    p_total, _ = hand_value(player_hand.cards)
    if d_total > 21:
        result = "Win"
        player.bankroll += player.bet
        stats["won"] += 1
    elif p_total > d_total:
        result = "Win"
        player.bankroll += player.bet
        stats["won"] += 1
    elif p_total < d_total:
        result = "Lose"
        player.bankroll -= player.bet
        stats["lost"] += 1
    else:
        result = "Push"
        stats["push"] += 1
    stats["played"] += 1
    print(f"{result}. Bankroll: {player.bankroll}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Blackjack (21) with Deck of Cards API")
    parser.add_argument("--decks", type=int, default=6, help="Number of decks (default 6)")
    parser.add_argument("--bet", type=int, default=10, help="Fixed bet per round")
    parser.add_argument("--bankroll", type=int, default=100, help="Starting bankroll")
    args = parser.parse_args()

    try:
        client = DeckClient(decks=args.decks)
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)

    player = Player("You", bankroll=args.bankroll, bet=args.bet)
    stats = {"played": 0, "won": 0, "lost": 0, "push": 0}

    while True:
        try:
            play_round(client, player, stats)
        except RuntimeError as exc:
            print(exc)
            raise SystemExit(1)
        cont = input("Continue? (y/n): ").strip().lower()
        if cont != "y":
            break

    print(f"Played: {stats['played']} | Won: {stats['won']} | Lost: {stats['lost']} | Push: {stats['push']} | Final bankroll: {player.bankroll}")


if __name__ == "__main__":
    main()
