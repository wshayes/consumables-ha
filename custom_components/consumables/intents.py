"""Intent handlers for the bundled sentence templates.

Registering these in Python is what removes `intent_script:` and `rest_command:` from
the customer's `configuration.yaml`. The bundled sentences match locally, land here,
and go straight to the API — no LLM, no YAML, no round trip beyond the one write.

Speech is composed here rather than server-side because these paths already know the
outcome; a second call to phrase a sentence we can already write would be latency the
user feels for nothing.
"""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent

from .const import (
    DOMAIN,
    INTENT_ADD,
    INTENT_ANSWER_LOCATION,
    INTENT_LIST_LOW,
    INTENT_QUERY,
    INTENT_REMOVE,
    INTENT_SET_STATE,
    INTENT_HASS_SHOP_ADD,
    INTENT_SHOP_ADD,
    INTENT_SHOP_CHECK,
    INTENT_SHOP_LIST,
)

_LOGGER = logging.getLogger(__name__)


def _client_for(hass: HomeAssistant):
    """The single paired household. One config entry per HA instance is the norm."""
    entries = list(hass.data.get(DOMAIN, {}).values())
    if not entries:
        raise intent.IntentHandleError("Consumables is not set up yet")
    return entries[0]


def _device_of(intent_obj: intent.Intent) -> str:
    """Name the satellite so the history shows where an update came from."""
    return intent_obj.device_id or "ha"


def _speak(intent_obj: intent.Intent, message: str) -> intent.IntentResponse:
    response = intent_obj.create_response()
    response.async_set_speech(message)
    return response


def _describe_failure(body: dict, spoken_name: str) -> str | None:
    """Turn a non-200 body into something worth saying, or None if it succeeded."""
    status = body.get("status", 200)
    if status == 200:
        return None
    if status == 409:
        candidates = body.get("candidates") or []
        if candidates:
            return f"Did you mean {' or '.join(candidates)}?"
        return "Which one did you mean?"
    if status == 404:
        # The server composes this one. An add for something never stocked comes back
        # 404 carrying a question ("Where does it live?") rather than a refusal, and
        # reading our own sentence over the top would throw the question away.
        if body.get("speech"):
            return body["speech"]
        return f"I don't have {spoken_name} in the inventory yet — add it in the app first."
    return "Sorry, I couldn't reach the inventory."


class _AddRemoveHandler(intent.IntentHandler):
    slot_schema = {
        vol.Required("item"): cv.string,
        vol.Optional("delta"): vol.Coerce(int),
    }

    def __init__(self, intent_type: str, sign: int) -> None:
        self.intent_type = intent_type
        self._sign = sign

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["item"]["value"]
        delta = abs(int(slots.get("delta", {}).get("value", 1) or 1)) * self._sign

        client = _client_for(intent_obj.hass)
        body = await client.adjust(name, delta=delta, source=_device_of(intent_obj))

        if (problem := _describe_failure(body, name)) is not None:
            return _speak(intent_obj, problem)

        item = body["item"]
        verb = "Added" if self._sign > 0 else "Removed"
        return _speak(intent_obj, f"{verb} {abs(delta)} {item['name']}. {item['display_quantity']} left.")


class _SetStateHandler(intent.IntentHandler):
    intent_type = INTENT_SET_STATE
    slot_schema = {
        vol.Required("item"): cv.string,
        vol.Required("state"): vol.In(["in_stock", "low", "out"]),
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["item"]["value"]
        state = slots["state"]["value"]

        client = _client_for(intent_obj.hass)
        body = await client.adjust(name, state=state, source=_device_of(intent_obj))

        if (problem := _describe_failure(body, name)) is not None:
            return _speak(intent_obj, problem)
        return _speak(intent_obj, f"Marked {body['item']['name']} as {state.replace('_', ' ')}.")


class _QueryHandler(intent.IntentHandler):
    intent_type = INTENT_QUERY
    slot_schema = {vol.Required("item"): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["item"]["value"]

        body = await _client_for(intent_obj.hass).query(name)
        if (problem := _describe_failure(body, name)) is not None:
            return _speak(intent_obj, problem)

        item = body["item"]
        return _speak(intent_obj, f"You have {item['display_quantity']} of {item['name']}.")


class _ListLowHandler(intent.IntentHandler):
    intent_type = INTENT_LIST_LOW
    slot_schema: dict = {}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        body = await _client_for(intent_obj.hass).low_stock()
        if body.get("status") != 200:
            return _speak(intent_obj, "Sorry, I couldn't reach the inventory.")

        names = [i["name"] for i in body.get("items", [])]
        if not names:
            return _speak(intent_obj, "Everything's stocked.")
        return _speak(intent_obj, f"Running low on {', '.join(names)}.")


class _ShoppingAddHandler(intent.IntentHandler):
    """Serves our own intent and Home Assistant's built-in `HassShoppingListAddItem`.

    HA ships its own sentences for "add X to the shopping list". They match the same
    literal text ours do, so which one wins is a coin flip decided by HA's matcher —
    and on an install with no `shopping_list` integration the built-in has no handler
    at all, so the household just hears "Unknown intent HassShoppingListAddItem".
    Answering HA's intent as well as ours makes both roads lead here, which is a
    better answer than asking people to unexpose a list entity they may not have.
    Its slot is `item`, the same one our sentences now use.

    ponytail: `HassListAddItem` (the modern todo-entity one) is deliberately left
    alone — HA core handles it, and overriding it would break real to-do lists.
    """

    slot_schema = {
        vol.Required("item"): cv.string,
        vol.Optional("delta"): vol.Coerce(int),
    }

    def __init__(self, intent_type: str) -> None:
        self.intent_type = intent_type

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["item"]["value"]
        qty = slots.get("delta", {}).get("value")

        body = await _client_for(intent_obj.hass).shopping_add(
            name, qty=int(qty) if qty else None, source=_device_of(intent_obj)
        )
        if body.get("status") not in (200, 201):
            return _speak(intent_obj, "Sorry, I couldn't add that to the list.")

        line = body.get("line") or {}
        return _speak(intent_obj, f"Added {line.get('name', name)} to the shopping list.")


class _AnswerLocationHandler(intent.IntentHandler):
    """The second turn of adding something the inventory had never seen.

    A plain follow-up utterance rather than a continued conversation: the bundled
    sentences match "in the fridge" on their own, so the household can answer at
    their own pace and the satellite needs no dialogue state. The server holds the
    half-made item and knows whether a question is actually open.
    """

    intent_type = INTENT_ANSWER_LOCATION
    slot_schema = {vol.Optional("storage"): cv.string, vol.Optional("location"): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        spoken = (slots.get("storage") or slots.get("location") or {}).get("value", "")

        body = await _client_for(intent_obj.hass).answer_location(spoken, source=_device_of(intent_obj))
        if body.get("status") != 200:
            return _speak(intent_obj, "Sorry, I couldn't file that.")
        return _speak(intent_obj, body.get("speech") or "Done.")


class _ShoppingListHandler(intent.IntentHandler):
    intent_type = INTENT_SHOP_LIST
    slot_schema: dict = {}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        body = await _client_for(intent_obj.hass).shopping_list()
        if body.get("status") != 200:
            return _speak(intent_obj, "Sorry, I couldn't reach the shopping list.")

        names = [line["name"] for line in body.get("lines", [])]
        if not names:
            return _speak(intent_obj, "The shopping list is empty.")
        return _speak(intent_obj, f"On the list: {', '.join(names)}.")


class _ShoppingCheckHandler(intent.IntentHandler):
    intent_type = INTENT_SHOP_CHECK
    slot_schema = {vol.Required("item"): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        name = slots["item"]["value"]

        body = await _client_for(intent_obj.hass).shopping_check(name, source=_device_of(intent_obj))
        if (problem := _describe_failure(body, name)) is not None:
            return _speak(intent_obj, problem)
        return _speak(intent_obj, f"Checked off {body.get('line', {}).get('name', name)}.")


async def async_register_intents(hass: HomeAssistant) -> None:
    """Register every handler. Safe to call once per config entry setup."""
    for handler in (
        _AddRemoveHandler(INTENT_ADD, 1),
        _AddRemoveHandler(INTENT_REMOVE, -1),
        _SetStateHandler(),
        _QueryHandler(),
        _ListLowHandler(),
        _ShoppingAddHandler(INTENT_SHOP_ADD),
        _ShoppingAddHandler(INTENT_HASS_SHOP_ADD),
        _AnswerLocationHandler(),
        _ShoppingListHandler(),
        _ShoppingCheckHandler(),
    ):
        intent.async_register(hass, handler)
