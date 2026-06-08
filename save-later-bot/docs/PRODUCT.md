# Save Later Bot — Product Architecture

## Vision

Replace abuse of Telegram Saved Messages with a structured **Second Brain**:

save → inbox → process → retrieve.

## Retention Loops

1. **Inbox** — every save lands in inbox; `/inbox` is the weekly habit
2. **Daily review** — morning push (Readwise-style): resurface from archive + unread backlog
3. **Weekly digest** — Sunday summary drives re-engagement
4. **Reminders** — natural language + push notifications
5. **Collections** — auto-sort reduces friction vs manual tags

## Monetization

| Free | Pro |
|------|-----|
| 100 saves | 5000 saves |
| FTS search | Hybrid semantic search |
| Personal saves | Shared folders |
| Basic URL title | LLM summaries |

## Analytics (internal)

Events in `user_events`:

- `item_saved`, `item_deleted`, `search`, `inbox_viewed`
- `reminder_sent`, `digest_sent`, `daily_review_sent`, `daily_review_opened`
- `daily_review_spotlight`, `duplicate_url`
- Status transitions: `item_done`, `item_archived`, etc.

Metrics: DAU/WAU via `aggregate_retention_metrics()`.

Future: admin `/stats` command or export to Grafana.

## Roadmap (not implemented)

- Spaced repetition for revisit suggestions
- Browser extension forward
- Team workspaces
