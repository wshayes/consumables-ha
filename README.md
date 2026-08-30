# Consumables for Home Assistant

Keep your household inventory up to date by talking to a Home Assistant Voice device.

> "We're out of paper towels."
> "Add three paper towels to the pantry."
> "Add milk." — goes on the shopping list
> "What are we running low on?"

## Install

1. **HACS → Integrations → ⋮ → Custom repositories**, add this repository as an
   *Integration*, then install **Consumables**.
2. Restart Home Assistant.
3. **Settings → Devices & services → Add integration → Consumables**.
4. In Consumables on the web, go to **Voice → Connect Home Assistant** for a pairing
   code, and enter it along with your Consumables address.
5. Restart once more so Home Assistant picks up the sentence templates the
   integration installed.
6. **Turn off Home Assistant's own shopping list** — see below. This one is not
   optional.

There is no token to copy and nothing to paste into `configuration.yaml`.

## Turn off Home Assistant's own shopping list

> **⚠️ Consumables and Home Assistant's built-in shopping list collide.** Both claim
> "add milk" and "add milk to the shopping list". Which one wins is decided by
> Home Assistant's sentence matcher, not by either integration, so leaving both
> enabled makes those phrasings a coin flip — some of what you say lands on a list
> Consumables cannot see, and you find out at the shops.

Consumables replaces it rather than sitting alongside it. Its list is filtered by
store, fills itself from anything running low, and checking an item off restocks the
item it came from.

1. **Settings → Voice assistants**, then the **Expose** tab.
2. Find `todo.shopping_list` (older installs name it `shopping_list.shopping_list`).
3. Toggle it off.

The entity, its contents, and any automation or dashboard card using it all keep
working — Assist just stops targeting it. Flip the toggle back to undo.

If you would rather remove it entirely: **Settings → Devices & services → Local
To-do** (or **Shopping list** on older installs) → delete the entry. That does
delete whatever is on the list, so check it first.

## Set up your assistant

**Settings → Voice assistants**, then either:

- **Free and offline (recommended).** Leave your existing conversation agent as-is
  and turn on **Prefer handling commands locally**. Everyday phrases are matched on
  your own hardware in about a millisecond and cost nothing.
- **Add the fallback.** Select **Consumables** as the conversation agent to have
  unusual phrasings understood by the server. Keep *Prefer handling commands locally*
  on so the free path still runs first.

## How it works

Two layers, cheapest first:

| Layer | Handles | Where | Cost |
|---|---|---|---|
| Sentence templates | "we're out of X", "how much X do we have" | your hardware, offline | free |
| Conversation agent | anything the templates miss | Consumables server | per utterance |

Item names are sent as free text and resolved on the server against your inventory,
including nicknames. Nothing about your inventory is synced into Home Assistant, and
no vocabulary needs configuring here.

The first time an unfamiliar phrasing is worked out, the server remembers it as an
alias — so "loo roll" costs one round trip, once, and is free from then on.

## Notes

- **Bare "add milk" goes on the shopping list**, matching the habit Home Assistant's
  own list built. Say "add milk to the pantry" when you mean the inventory — that you
  already have it, rather than needing to buy it. Both are matched locally and free.
- **Rotating credentials.** Generating a new pairing code invalidates the old token.
  Re-run the integration setup with the new code.
- **Your data stays in your Consumables instance.** This integration talks only to
  the address you configured.

## Status

Scaffold — the code is complete but has not yet been exercised against a running
Home Assistant instance. Expect to shake out import paths and API details on first
install. Issues and PRs welcome.
