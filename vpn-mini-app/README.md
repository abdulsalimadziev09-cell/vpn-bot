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

### Продакшен (nexussvpn.ru + SSL)

Нужен VPS с Docker, домен `nexussvpn.ru`, бот и Mini App на **одной** машине.

#### 1. DNS у регистратора

| Запись | Тип | Значение |
|--------|-----|----------|
| `@` | A | IP вашего VPS |
| `www` | A | тот же IP (или CNAME → `nexussvpn.ru`) |

Подождите 5–30 минут, пока DNS обновится:

```bash
dig +short www.nexussvpn.ru
```

#### 2. Фаервол на VPS

Откройте **80** и **443** (для Let's Encrypt и HTTPS):

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload
```

Порты бота (`8080`) и VPN (`42923/udp`) можно не трогать — Mini App идёт через 443.

#### 3. Mini App с автоматическим SSL (Caddy)

На VPS, в каталоге `vpn-mini-app`:

```bash
cd vpn-mini-app
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy сам выпустит сертификат для `www.nexussvpn.ru` и `nexussvpn.ru`.
Локальный `docker compose up` (порт `8081`) для прода **не** нужен — остановите, если мешает:

```bash
docker compose down
```

Проверка:

```bash
curl -I https://www.nexussvpn.ru/
curl https://www.nexussvpn.ru/lava-verify_751e93edad61d6f3.html
```

#### 4. Подключить к боту

В `vpn-sales-bot/.env` на VPS:

```env
MINI_APP_URL=https://www.nexussvpn.ru/
```

Перезапуск бота:

```bash
cd ../vpn-sales-bot
docker compose up -d --build
```

#### 5. Telegram BotFather

В [@BotFather](https://t.me/BotFather) для `@nexussvpnbot`:

1. `/setdomain` → выберите бота → введите `www.nexussvpn.ru`
2. `/setmenubutton` (опционально) → URL: `https://www.nexussvpn.ru/`

В боте появится кнопка **«Открыть приложение»**.

> **Важно:** URL в `MINI_APP_URL`, домен в BotFather и домен в `Caddyfile` должны совпадать (`www.nexussvpn.ru`).

#### Другой домен

Отредактируйте `Caddyfile`, затем `docker compose -f docker-compose.prod.yml up -d --build`.

## Связь с ботом

Mini App отправляет JSON в бот:

| action | Что делает бот |
|--------|----------------|
| `select_plan` + `plan_code` | Создаёт заказ и шлёт инвойс Stars |
| `trial` | Активирует пробный период |
| `my_subscription` | Показывает статус подписки |
| `referral` | Показывает реферальную ссылку |

Обработчик: `vpn-sales-bot/app/bot/handlers/mini_app.py`
