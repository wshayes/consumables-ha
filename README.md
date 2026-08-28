# Consumables for Home Assistant

Keep your household inventory up to date by talking to a Home Assistant Voice device.

> "We're out of paper towels."
> "Add three paper towels to the pantry."
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

- **"add milk" is deliberately not matched.** It collides with Home Assistant's own
  shopping-list intent. Say "add milk to the pantry", or let it fall through to the
  conversation agent.
- **Rotating credentials.** Generating a new pairing code invalidates the old token.
  Re-run the integration setup with the new code.
- **Your data stays in your Consumables instance.** This integration talks only to
  the address you configured.

## Status

Scaffold — the code is complete but has not yet been exercised against a running
Home Assistant instance. Expect to shake out import paths and API details on first
install. Issues and PRs welcome.
