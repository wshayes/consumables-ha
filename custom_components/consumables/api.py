"""Thin async client for the Consumables API.

Every call carries the household's bridge token and nothing else — the token *is*
the tenant identifier, so there is no household to name and no way for a misconfigured
instance to address someone else's data.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    PATH_ADJUST,
    PATH_ANSWER_LOCATION,
    PATH_INTERPRET,
    PATH_LOW,
    PATH_PAIR,
    PATH_QUERY,
    PATH_SHOPPING,
    PATH_SHOPPING_ADD,
    PATH_SHOPPING_CHECK,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class ConsumablesError(Exception):
    """Any failure talking to the server."""


class InvalidPairingCode(ConsumablesError):
    """The code was wrong, already used, or expired."""


class CannotConnect(ConsumablesError):
    """The server was unreachable or returned something unusable."""


async def redeem_pairing_code(
    session: aiohttp.ClientSession, base_url: str, code: str
) -> dict[str, Any]:
    """Trade a short pairing code for a long-lived bridge token."""
    url = f"{base_url.rstrip('/')}{PATH_PAIR}"
    try:
        async with session.post(
            url, json={"code": code}, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        ) as response:
            if response.status == 404:
                raise InvalidPairingCode("pairing code is invalid or has expired")
            if response.status != 200:
                raise CannotConnect(f"pairing failed with HTTP {response.status}")
            return await response.json()
    except aiohttp.ClientError as err:
        raise CannotConnect(str(err)) from err


class ConsumablesClient:
    """Authenticated calls for one household."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base}{path}"
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                **kwargs,
            ) as response:
                body = await response.json()
                if response.status >= 400:
                    # 404 and 409 are ordinary conversational outcomes — an unknown
                    # item, or one that needs disambiguating — so hand the body back
                    # and let the caller turn it into something worth saying.
                    body.setdefault("status", response.status)
                    return body
                body["status"] = response.status
                return body
        except aiohttp.ClientError as err:
            raise CannotConnect(str(err)) from err

    async def adjust(
        self, name: str, *, delta: int | None = None, state: str | None = None, source: str = "ha"
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "source": source, "reason": "voice"}
        if delta is not None:
            payload["delta"] = delta
        if state is not None:
            payload["state"] = state
        return await self._request("POST", PATH_ADJUST, json=payload)

    async def answer_location(self, location: str, *, source: str = "ha") -> dict[str, Any]:
        """Where a newly added item lives — the second half of a two-turn add."""
        return await self._request("POST", PATH_ANSWER_LOCATION, json={"location": location, "source": source})

    async def query(self, name: str) -> dict[str, Any]:
        return await self._request("GET", PATH_QUERY, params={"name": name})

    async def low_stock(self) -> dict[str, Any]:
        return await self._request("GET", PATH_LOW)

    async def shopping_list(self) -> dict[str, Any]:
        return await self._request("GET", PATH_SHOPPING)

    async def shopping_add(self, name: str, *, qty: int | None = None, source: str = "ha") -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "source": source}
        if qty is not None:
            payload["qty"] = qty
        return await self._request("POST", PATH_SHOPPING_ADD, json=payload)

    async def shopping_check(self, name: str, *, source: str = "ha") -> dict[str, Any]:
        return await self._request("POST", PATH_SHOPPING_CHECK, json={"name": name, "source": source})

    async def interpret(self, text: str, device_id: str = "ha") -> dict[str, Any]:
        """Ask the server to work out an utterance the local templates didn't match."""
        return await self._request("POST", PATH_INTERPRET, json={"text": text, "device_id": device_id})

    async def async_check_credentials(self) -> bool:
        """Cheap round-trip to confirm the token still works."""
        result = await self.low_stock()
        return result.get("status") == 200
