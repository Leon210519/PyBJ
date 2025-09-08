from __future__ import annotations

from dataclasses import dataclass
import time
import typing as t

import requests


@dataclass
class Card:
    code: str
    value: str
    suit: str
    image: str


class DeckClient:
    def __init__(self, decks: int = 6, session: t.Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        url = f"https://www.deckofcardsapi.com/api/deck/new/shuffle/?deck_count={decks}"
        resp = self._request("GET", url)
        data = resp.json()
        deck_id = data.get("deck_id")
        remaining = data.get("remaining")
        if not deck_id or remaining is None:
            raise RuntimeError("Invalid response from Deck API when creating deck")
        self.deck_id = str(deck_id)
        self.initial_remaining = 52 * decks
        self._remaining = int(remaining)

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
        url = f"https://www.deckofcardsapi.com/api/deck/{self.deck_id}/draw/?count={n}"
        resp = self._request("GET", url)
        data = resp.json()
        cards = data.get("cards")
        remaining = data.get("remaining")
        if cards is None or remaining is None:
            raise RuntimeError("Invalid response from Deck API when drawing cards")
        self._remaining = int(remaining)
        return [Card(code=c["code"], value=c["value"], suit=c["suit"], image=c["image"]) for c in cards]

    def reshuffle_remaining(self) -> None:
        url = f"https://www.deckofcardsapi.com/api/deck/{self.deck_id}/shuffle/?remaining=true"
        resp = self._request("GET", url)
        data = resp.json()
        remaining = data.get("remaining")
        if remaining is None:
            raise RuntimeError("Invalid response from Deck API when reshuffling")
        self._remaining = int(remaining)
