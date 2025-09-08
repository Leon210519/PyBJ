# blackjack.py
"""
Minimal starting point for a Blackjack (21) CLI using the Deck of Cards API.
This file is intentionally simple so Codex can expand it.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Play Blackjack (21) with Deck of Cards API")
    parser.add_argument("--decks", type=int, default=6, help="Number of decks (default 6)")
    parser.add_argument("--bet", type=int, default=10, help="Fixed bet per round")
    parser.add_argument("--bankroll", type=int, default=100, help="Starting bankroll")
    args = parser.parse_args()

    print("Blackjack starting...")
    print(f"Decks: {args.decks}, Bet: {args.bet}, Bankroll: {args.bankroll}")
    # TODO: integrate DeckClient, deal cards, implement game loop


if __name__ == "__main__":
    main()
