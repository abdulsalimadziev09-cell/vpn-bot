# vpn-bot

Telegram VPN-магазин на AmneziaWG.

## Проекты

| Папка | Описание |
|-------|----------|
| [`vpn-sales-bot/`](vpn-sales-bot/) | Python-бот: Stars, подписки, выдача конфигов |
| [`vpn-mini-app/`](vpn-mini-app/) | Telegram Mini App с UI для тарифов и настройки |

## Быстрый старт

```bash
cd vpn-sales-bot
cp .env.example .env
docker compose up -d --build

cd ../vpn-mini-app
npm install && npm run build
docker compose up -d --build
```

В `.env` бота добавьте URL Mini App:

```env
MINI_APP_URL=https://your-domain.example/
```
