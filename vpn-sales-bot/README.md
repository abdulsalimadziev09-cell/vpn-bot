# VPN Sales Bot

Telegram-бот для продажи VPN-подписок на базе Amnezia. Оплата через **Telegram Stars**, выдача персональных конфигов, продление и автоотключение по сроку.

## Возможности

- Тарифы: 1 мес / 3 мес / 1 год (цены в Stars настраиваются в БД)
- Оплата Telegram Stars (встроенные инвойсы, без внешних платёжек)
- Выдача `.conf` и QR в Telegram
- Ручная выдача (MVP), SSH-скрипт или amnezia-api
- Пробный период 1 день (один раз на пользователя)
- Напоминания за 7, 3 и 1 день до конца подписки
- Автоотключение просроченных клиентов

## Быстрый старт

```bash
cd vpn-sales-bot
cp .env.example .env
# заполните BOT_TOKEN, ADMIN_IDS

docker compose up -d --build
```

Локально без Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d postgres
alembic upgrade head
python -m app.main
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_IDS` | Telegram ID админов через запятую |
| `PAYMENTS_ENABLED` | Включить оплату Stars |
| `MINI_APP_URL` | HTTPS-URL Telegram Mini App (кнопка «Открыть приложение») |
| `VPN_PROVISIONER` | `manual` / `ssh` / `amnezia_api` |

## Telegram Mini App

UI в папке [`../vpn-mini-app/`](../vpn-mini-app/). После деплона на HTTPS-домен укажите `MINI_APP_URL` в `.env`.

## Telegram Stars

Оплата полностью внутри Telegram — домен и HTTPS для webhooks **не нужны**.

1. В [@BotFather](https://t.me/BotFather) включите платежи для бота (Stars).
2. Пользователь выбирает тариф → получает инвойс → оплачивает Stars.
3. Бот автоматически активирует подписку и выдаёт конфиг.

Цены в Stars хранятся в таблице `plans` (`stars_price`):

| Тариф | Stars (по умолчанию) |
|-------|----------------------|
| 1 месяц | 150 |
| 3 месяца | 400 |
| 1 год | 1000 |

Изменить цены:

```sql
UPDATE plans SET stars_price = 60 WHERE code = 'month_1';
```

## Режимы выдачи VPN

### manual (по умолчанию)

После оплаты админ получает уведомление. На VPS создайте клиента вручную, затем:

```
/admin_approve <order_id>
```

и отправьте содержимое `.conf`.

### ssh

```env
VPN_PROVISIONER=ssh
SSH_HOST=your-vps-ip
SSH_USER=deploy
SSH_KEY_PATH=/app/keys/vps_ed25519
SSH_ADD_CLIENT_SCRIPT=/opt/awg/amneziawg-install.sh
```

### amnezia_api

```env
VPN_PROVISIONER=amnezia_api
AMNEZIA_API_URL=https://your-vps.example:8081
AMNEZIA_API_KEY=secret
```

## Команды бота

| Команда | Действие |
|---------|----------|
| `/start` | Меню и тарифы |
| `/my` | Статус подписки |
| `/help` | FAQ и инструкция AmneziaVPN |
| Меню «🎁 Туннелирование» | Список `amnezia_sites.json` для раздельного туннелирования (подарок после выдачи конфига) |
| `/admin` | Все админ-команды (только для ADMIN_IDS) |
| `/admin_subscriptions` | Сводка: у кого сколько дней осталось (админ) |
| `/admin_orders` | Заказы, ожидающие выдачи (админ) |
| `/admin_approve <id>` | Ручная выдача конфига (админ) |

## Тесты

```bash
pytest
```

## Архитектура

```
Handlers → Services → Repositories → PostgreSQL
              ↓
       Telegram Stars + VpnProvisioner + Scheduler
```
