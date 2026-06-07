# Nexus VPN — Telegram Mini App

Красивое веб-приложение для бота `@nexussvpnbot`: тарифы, преимущества, инструкция по подключению.

## Возможности

- Тёмный UI с градиентами (Amnezia / VPN стиль)
- Вкладки: **Тарифы**, **Плюсы**, **Настройка**
- Оплата через `sendData` → бот выставляет инвойс Stars
- Кнопки: пробный период, моя подписка, рефералка
- Файл `lava-verify_*.html` в `public/` для верификации домена

## Локальная разработка

```bash
cd vpn-mini-app
npm install
npm run dev
```

Откройте `http://localhost:5173`. Вне Telegram кнопки оплаты показывают демо-баннер.

## Сборка

```bash
npm run build
```

Статика в `dist/`.

## Деплой

### Docker

```bash
docker compose up -d --build
```

Mini App на `http://localhost:8081`.

### Продакшен

1. Соберите и разместите `dist/` на домене с **HTTPS**
2. В `.env` бота укажите:

```env
MINI_APP_URL=https://your-domain.example/
```

3. В [@BotFather](https://t.me/BotFather):
   - `/setdomain` — привяжите тот же домен к боту
   - `/setmenubutton` — URL Mini App (опционально)

4. Проверка Lava:

```bash
curl https://your-domain.example/lava-verify_751e93edad61d6f3.html
```

## Связь с ботом

Mini App отправляет JSON в бот:

| action | Что делает бот |
|--------|----------------|
| `select_plan` + `plan_code` | Создаёт заказ и шлёт инвойс Stars |
| `trial` | Активирует пробный период |
| `my_subscription` | Показывает статус подписки |
| `referral` | Показывает реферальную ссылку |

Обработчик: `vpn-sales-bot/app/bot/handlers/mini_app.py`
