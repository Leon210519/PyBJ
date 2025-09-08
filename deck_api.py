from __future__ import annotations

from dataclasses import dataclass
import time
import typing as t
import random

import requests


@dataclass
class Card:
    code: str
    value: str
    suit: str
    image: str


class DeckClient:
    def __init__(self, decks: int = 6, session: t.Optional[requests.Session] = None) -> None:
        """Client for drawing cards.

        The class primarily talks to deckofcardsapi.com but falls back to a
        simple local deck when the API is unreachable (common in offline
        environments).  The public interface is compatible in both modes.
        """

        self.session = session or requests.Session()
        url = f"https://www.deckofcardsapi.com/api/deck/new/shuffle/?deck_count={decks}"
        try:
            resp = self._request("GET", url)
            data = resp.json()
            deck_id = data.get("deck_id")
            remaining = data.get("remaining")
            if not deck_id or remaining is None:
                raise RuntimeError
            self.deck_id = str(deck_id)
            self.initial_remaining = 52 * decks
            self._remaining = int(remaining)
            self._api_mode = True
        except Exception:
            # fall back to a local shuffled deck
            self.deck_id = "local"
            self.initial_remaining = 52 * decks
            self._cards = self._generate_deck(decks)
            self._remaining = len(self._cards)
            self._api_mode = False

    @property
    def remaining(self) -> int:
        return self._remaining

    def _request(
        self,
        method: str,
        url: str,
        *,
        retries: int = 3,
        timeout: float = 10.0,
        **kwargs: t.Any,
    ) -> requests.Response:
        backoff = 0.5
        last_exc: t.Optional[Exception] = None
        for attempt in range(retries):
            try:
                resp = self.session.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code >= 400:
                    snippet = resp.text[:100]
                    raise RuntimeError(f"Deck API error {resp.status_code}: {snippet}")
                return resp
            except requests.RequestException as exc:  # network error
                last_exc = exc
                if attempt == retries - 1:
                    break
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError(f"Network error contacting Deck API: {last_exc}")

    def draw(self, n: int = 1) -> list[Card]:
        if self._api_mode:
            url = f"https://www.deckofcardsapi.com/api/deck/{self.deck_id}/draw/?count={n}"
            resp = self._request("GET", url)
            data = resp.json()
            cards = data.get("cards")
            remaining = data.get("remaining")
            if cards is None or remaining is None:
                raise RuntimeError("Invalid response from Deck API when drawing cards")
            self._remaining = int(remaining)
            return [Card(code=c["code"], value=c["value"], suit=c["suit"], image=c["image"]) for c in cards]

        # local mode
        draw_cards = self._cards[:n]
        self._cards = self._cards[n:]
        self._remaining = len(self._cards)
        return draw_cards

    def reshuffle_remaining(self) -> None:
        if self._api_mode:
            url = f"https://www.deckofcardsapi.com/api/deck/{self.deck_id}/shuffle/?remaining=true"
            resp = self._request("GET", url)
            data = resp.json()
            remaining = data.get("remaining")
            if remaining is None:
                raise RuntimeError("Invalid response from Deck API when reshuffling")
            self._remaining = int(remaining)
            return

        # local mode: rebuild and shuffle full deck
        decks = self.initial_remaining // 52
        self._cards = self._generate_deck(decks)
        self._remaining = len(self._cards)

    def _generate_deck(self, decks: int) -> list[Card]:
        """Generate a shuffled list of ``Card`` objects for ``decks`` decks."""
        suits = ["SPADES", "HEARTS", "CLUBS", "DIAMONDS"]
        values = ["ACE", "2", "3", "4", "5", "6", "7", "8", "9", "10", "JACK", "QUEEN", "KING"]
        cards: list[Card] = []
        for _ in range(decks):
            for suit in suits:
                for value in values:
                    code_value = value[0]
                    if value == "10":
                        code_value = "0"
                    code = f"{code_value}{suit[0]}"
                    image = f"https://deckofcardsapi.com/static/img/{code}.png"
                    cards.append(Card(code=code, value=value, suit=suit, image=image))
        random.shuffle(cards)
        return cards
