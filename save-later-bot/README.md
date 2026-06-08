# Save Later Bot — Telegram Second Brain

Save links, notes, forwards, voice → tag, search, remind, process inbox.

## Product pillars

| Pillar | Features |
|--------|----------|
| Capture | Links, text, forwards, voice + Whisper transcription |
| Process | Inbox → Reading → Done → Archived |
| Retrieve | FTS + Pro semantic search, collections, tags |
| Retention | Daily review (morning), weekly digest, smart reminders |
| Monetize | Free limits, Pro via Telegram Stars |

## Quick start

```bash
cp .env.example .env
docker compose up -d --build
alembic upgrade head   # auto in entrypoint
```

Requires `pgvector/pgvector:pg16` (included in docker-compose).

## Commands

| Command | Action |
|---------|--------|
| `/inbox` | Items to process |
| `/daily` | Morning review (archive + unread); `/daily off` to disable |
| `/done <id>` / `/archive <id>` | Status workflow |
| `/delete <id>` | Remove item |
| `/search <query>` | FTS (Pro: + semantic) |
| `/pro` / `/buy` | Plan & Stars payment |
| `/folder *` | Shared folders (Pro) |

**Natural reminders:** «напомни завтра», «remind next week», «напомни через 3 дня»

**Collections (auto):** Read Later, Startup Ideas, Books, Travel, Buy Later, Research

## Architecture

```
Handlers → Services (orchestrator) → Repositories → PostgreSQL
                ↓
         Analytics events, Scheduler (reminders, digest, plan expiry)
```

See [docs/PRODUCT.md](docs/PRODUCT.md) and [docs/IMPORT_SAVED_MESSAGES.md](docs/IMPORT_SAVED_MESSAGES.md).

## Env

| Variable | Default |
|----------|---------|
| `BOT_TOKEN` | required |
| `OPENAI_API_KEY` | embeddings + Pro URL summaries |
| `FREE_ITEM_LIMIT` / `PRO_ITEM_LIMIT` | 100 / 5000 |
| `DIGEST_DAY_OF_WEEK` / `DIGEST_HOUR` | sun / 7 UTC |
| `DAILY_REVIEW_HOUR` | 5 UTC (~08:00 MSK) |

## Tests

```bash
pytest   # 35+ unit tests
```

## Migrations

- `001` — MVP schema
- `002` — Pro, folders, embeddings
- `003` — Inbox, collections, analytics, URL summaries, HNSW index
- `004` — Daily review setting
