"""Consumables — household inventory by voice.

Setting up a config entry does three things:

1. builds an authenticated client from the token the pairing flow obtained,
2. registers the intent handlers the bundled sentences target, and
3. copies those sentences into the config directory so Home Assistant's own matcher
   picks them up.

Step 3 is the one piece that isn't purely in-process: Home Assistant only reads
sentence templates from `<config>/custom_sentences/<lang>/`, and there is no
supported way for an integration to register them in memory. Writing the file at
setup is the honest version of "paste this into your config" — it just doesn't make
the customer do it.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, ConsumablesClient
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN
from .intents import async_register_intents

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]

SENTENCE_LANGUAGES = ("en",)


def _install_sentences(config_dir: str) -> None:
    """Copy bundled sentence templates into <config>/custom_sentences/<lang>/.

    Overwrites on every setup so an integration update ships template fixes. The file
    is namespaced by our domain, so nothing else in that directory is touched.
    """
    source_root = Path(__file__).parent / "custom_sentences"
    for language in SENTENCE_LANGUAGES:
        source = source_root / language / f"{DOMAIN}.yaml"
        if not source.is_file():
            continue
        destination_dir = Path(config_dir) / "custom_sentences" / language
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination_dir / f"{DOMAIN}.yaml")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = ConsumablesClient(
        async_get_clientsession(hass),
        entry.data[CONF_BASE_URL],
        entry.data[CONF_TOKEN],
    )

    try:
        if not await client.async_check_credentials():
            # The token was rotated on the server — re-pairing is the fix, so ask for
            # it rather than retrying a credential that will never work again.
            entry.async_start_reauth(hass)
            return False
    except CannotConnect as err:
        raise ConfigEntryNotReady(f"Consumables server unreachable: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    await hass.async_add_executor_job(_install_sentences, hass.config.config_dir)
    await async_register_intents(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Consumables ready — sentences installed; restart to load them if this is a first install")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
