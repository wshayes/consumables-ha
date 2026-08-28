"""Conversation agent for utterances the sentence templates don't match.

This is the paid path, so it should run as rarely as possible. Select this agent for
your assistant and leave *Prefer handling commands locally* on: Home Assistant then
tries its own intents and the bundled Consumables sentences first, and only what
nothing matched reaches here.

The server does the interpreting — it has the household's item list and can resolve a
spoken phrase against names and aliases. All this class does is carry one sentence
there and speak what comes back.
"""

from __future__ import annotations

import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CannotConnect
from .const import CONF_TENANT, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([ConsumablesConversationEntity(entry, hass.data[DOMAIN][entry.entry_id])])


class ConsumablesConversationEntity(conversation.ConversationEntity):
    """Sends one sentence to the Consumables server and speaks the reply."""

    _attr_has_entity_name = True
    _attr_name = "Consumables"

    def __init__(self, entry: ConfigEntry, client) -> None:
        self._entry = entry
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}-conversation"

    @property
    def supported_languages(self) -> list[str]:
        # The server prompt is English; add languages here as the prompt grows them.
        return ["en"]

    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        intent_response = conversation.intent.IntentResponse(language=user_input.language)

        try:
            body = await self._client.interpret(
                user_input.text, device_id=user_input.device_id or "ha"
            )
        except CannotConnect as err:
            _LOGGER.warning("could not reach Consumables: %s", err)
            intent_response.async_set_speech("Sorry, I couldn't reach the inventory.")
            return conversation.ConversationResult(
                response=intent_response, conversation_id=user_input.conversation_id
            )

        if body.get("status") == 503:
            # The server has no model key configured. Say something true rather than
            # implying the request was understood.
            speech = "Voice understanding isn't set up on the server yet."
        else:
            speech = body.get("speech") or "Sorry, I didn't catch that."

        intent_response.async_set_speech(speech)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=user_input.conversation_id
        )
