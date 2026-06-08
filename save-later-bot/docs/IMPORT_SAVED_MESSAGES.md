# Import from Telegram Saved Messages

## Feasibility

**Bot API cannot read Saved Messages.** The favorites chat is private to the user session, not accessible to bots.

## Options

### 1. Manual forward (supported today)

User forwards messages from Saved Messages to the bot. Existing `extractor` + `SaveOrchestrator` handle them.

### 2. MTProto user client (future CLI)

Use Telethon or Pyrogram with **user** credentials (not bot token):

```bash
# Planned: scripts/import_saved_messages.py
python scripts/import_saved_messages.py --session user.session --limit 500
```

Flow:

1. User authorizes via phone + 2FA once
2. Script reads `me` → Saved Messages chat
3. Maps messages to `SavePayload`
4. Bulk insert via repository layer
5. Optional embedding backfill job for Pro users

Risks: ToS, rate limits, media storage, duplicates.

### 3. Export file import (future)

Telegram Desktop export → JSON → `/import` bot command accepting document.

## Recommendation

Start with **forward** for MVP. Add MTProto CLI when import volume justifies maintenance.
