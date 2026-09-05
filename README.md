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

There is no token to copy and nothing to paste into `configuration.yaml`.

## Home Assistant's own shopping list

Home Assistant ships sentences for "add milk to the shopping list" too, and they
match the same words ours do — so which one wins is decided by HA's matcher, not by
either integration. **You do not have to do anything about this.** Consumables
answers HA's `HassShoppingListAddItem` as well as its own intent, so both roads lead
to your Consumables list.

(Before v0.1.2 they did not, and on an install with no shopping-list integration set
up the collision produced a spoken `Unknown intent HassShoppingListAddItem` with no
log entry to explain it.)

If you keep a **to-do list entity** (`todo.shopping_list`) and would rather Assist
stopped targeting it, **Settings → Voice assistants → Expose** and toggle it off.
That is a preference now, not a fix: the entity, its contents, and any automation or
dashboard card using it all keep working either way.

Consumables replaces it rather than sitting alongside it. Its list is filtered by
store, fills itself from anything running low, and checking an item off restocks the
item it came from.

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

First run against a real Home Assistant instance: 2026-09-05. Two bugs found and
fixed in v0.1.2:

- **The spoken item slot could not be called `name`.** HA reserves that slot for its
  own list of exposed entity names and silently overrides a wildcard declared in a
  custom sentence file, so every sentence with an item in it stopped matching
  groceries and answered "I am not aware of any device called eggs". The slot is
  `item` now. Sentences with no item in them ("what are we running low on") always
  worked, which is what made this look like a partial install rather than a bug.
- **`HassShoppingListAddItem` had no handler.** See above.

Issues and PRs welcome.
