"""Setup dialog: two fields, no tokens to copy.

The customer generates a code on the Consumables website (Voice → Connect Home
Assistant) and types it in here. We exchange it for the household's bridge token and
store that in the config entry, so the token never has to be seen, pasted, or kept in
`secrets.yaml`.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidPairingCode, redeem_pairing_code
from .const import CONF_BASE_URL, CONF_PAIRING_CODE, CONF_TENANT, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL): str,
        vol.Required(CONF_PAIRING_CODE): str,
    }
)


def _normalise_base_url(raw: str) -> str:
    """Accept what people actually type: bare hosts, trailing slashes, whitespace."""
    url = raw.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


class ConsumablesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pair one household."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = _normalise_base_url(user_input[CONF_BASE_URL])
            code = user_input[CONF_PAIRING_CODE]
            session = async_get_clientsession(self.hass)

            try:
                result = await redeem_pairing_code(session, base_url, code)
            except InvalidPairingCode:
                errors["base"] = "invalid_code"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 — surface as a generic error, never a traceback
                _LOGGER.exception("unexpected error while pairing")
                errors["base"] = "unknown"
            else:
                tenant = result["tenant"]
                # One entry per household, so re-running setup re-pairs rather than
                # silently creating a second entry with a now-dead token.
                await self.async_set_unique_id(f"{base_url}::{tenant}")
                self._abort_if_unique_id_configured(
                    updates={CONF_TOKEN: result["token"], CONF_BASE_URL: base_url}
                )
                return self.async_create_entry(
                    title=result.get("name") or tenant,
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_TOKEN: result["token"],
                        CONF_TENANT: tenant,
                    },
                )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Tokens are rotated by re-pairing, so reauth is just the same form again."""
        return await self.async_step_user()
