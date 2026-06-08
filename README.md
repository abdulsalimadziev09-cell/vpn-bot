# vpn-bot

Telegram VPN-магазин на AmneziaWG + обменник Stars.

## Проекты

| Папка | Описание | Порт |
|-------|----------|------|
| [`vpn-sales-bot/`](vpn-sales-bot/) | Python-бот: Stars, подписки, выдача конфигов | `8080` |
| [`vpn-mini-app/`](vpn-mini-app/) | Telegram Mini App с UI для тарифов | `8081` |
| [`stars-exchange-bot/`](stars-exchange-bot/) | Обменник: рубли → Stars через Robokassa | `8081` |

> **Порт 8081** занят и Mini App, и stars-exchange-bot. На одной машине поднимайте оба через reverse proxy с разными доменами или поменяйте порт в `docker-compose.yml` одного из проектов (например Mini App → `8082:80`).

## Быстрый старт (все три)

### 1. Подготовка `.env`

```bash
cd vpn-sales-bot && cp .env.example .env
cd ../stars-exchange-bot && cp .env.example .env
cd ..
```

Заполните в каждом `.env` свои `BOT_TOKEN`, `ADMIN_IDS` и остальные переменные (см. README внутри папок).

### 2. VPN-бот + Mini App

```bash
# VPN sales bot (postgres :5433, HTTP :8080)
cd vpn-sales-bot
docker compose up -d --build

# Mini App (статика, :8081)
cd ../vpn-mini-app
npm install && npm run build
docker compose up -d --build
```

В `vpn-sales-bot/.env` укажите URL Mini App:

```env
MINI_APP_URL=https://your-domain.example/
```

### 3. Обменник Stars

```bash
cd stars-exchange-bot
docker compose up -d --build
```

В Robokassa укажите `PUBLIC_BASE_URL` из `.env` (Result/Success/Fail URL — см. [`stars-exchange-bot/README.md`](stars-exchange-bot/README.md)).

### Запуск одной цепочкой

Из корня репозитория:

```bash
(cd vpn-sales-bot && cp -n .env.example .env; docker compose up -d --build) && \
(cd vpn-mini-app && npm install && npm run build && docker compose up -d --build) && \
(cd stars-exchange-bot && cp -n .env.example .env; docker compose up -d --build)
```

`cp -n` не перезапишет уже существующий `.env`.

## Остановка

```bash
cd vpn-sales-bot && docker compose down
cd ../vpn-mini-app && docker compose down
cd ../stars-exchange-bot && docker compose down
```

## Логи и статус

```bash
docker compose -f vpn-sales-bot/docker-compose.yml ps
docker compose -f vpn-sales-bot/docker-compose.yml logs -f bot

docker compose -f vpn-mini-app/docker-compose.yml logs -f mini-app

docker compose -f stars-exchange-bot/docker-compose.yml ps
docker compose -f stars-exchange-bot/docker-compose.yml logs -f bot
```

## Порты (локально)

| Сервис | Порт |
|--------|------|
| vpn-sales-bot HTTP | `8080` |
| vpn-sales-bot PostgreSQL | `5433` |
| vpn-mini-app | `8081` |
| stars-exchange-bot HTTP | `8081` |
| stars-exchange-bot PostgreSQL | `5434` |

Подробности — в README каждого проекта.
