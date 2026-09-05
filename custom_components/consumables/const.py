"""Shared constants for the Consumables integration."""

from __future__ import annotations

DOMAIN = "consumables"

CONF_BASE_URL = "base_url"
CONF_PAIRING_CODE = "pairing_code"
CONF_TOKEN = "token"
CONF_TENANT = "tenant"

# Server endpoints. The bridge token identifies the household on its own, so none of
# these take a tenant parameter.
PATH_PAIR = "/app/api/pair"
PATH_ADJUST = "/app/api/inventory/adjust"
PATH_QUERY = "/app/api/inventory/query"
PATH_ANSWER_LOCATION = "/app/api/inventory/answer-location"
PATH_LOW = "/app/api/inventory/low"
PATH_INTERPRET = "/app/api/voice/interpret"
PATH_SHOPPING = "/app/api/shopping"
PATH_SHOPPING_ADD = "/app/api/shopping/add"
PATH_SHOPPING_CHECK = "/app/api/shopping/check"

# Intents handled locally by the bundled sentence templates. These are registered in
# Python rather than through intent_script/rest_command YAML, so installing the
# integration is the whole setup — there is nothing to paste into configuration.yaml.
INTENT_ADD = "AddConsumable"
INTENT_REMOVE = "RemoveConsumable"
INTENT_SET_STATE = "SetConsumableState"
INTENT_QUERY = "QueryConsumable"
# "Where is the butter?" — reads the same row as QueryConsumable and phrases the
# other half of it, so it needs no endpoint of its own.
INTENT_WHERE = "WhereConsumable"
INTENT_LIST_LOW = "ListLowStock"
INTENT_SHOP_ADD = "AddToShoppingList"
INTENT_SHOP_LIST = "ListShopping"
INTENT_SHOP_CHECK = "CheckOffShopping"
# Home Assistant's own legacy shopping-list intent. Its built-in sentences claim
# "add X to the shopping list" and outrank ours, so we answer it too rather than
# leaving it to fail as "Unknown intent" on installs with no shopping_list set up.
INTENT_HASS_SHOP_ADD = "HassShoppingListAddItem"
# Answering "where does it live?" after adding something never stocked before.
INTENT_ANSWER_LOCATION = "AnswerLocation"

REQUEST_TIMEOUT = 15
