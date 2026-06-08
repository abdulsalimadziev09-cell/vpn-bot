# Stars Exchange Bot

Telegram-бот: покупка **Telegram Stars** за рубли через **Robokassa**.

## Возможности

- Пакеты Stars и произвольная сумма (курс в `.env`)
- Оплата картой / СБП через Robokassa
- Получатель — себе или любой `@username`
- Выдача Stars: **manual** (админ) или **telethon** (авто через MTProto)
- Webhook Result URL для подтверждения оплаты

## Быстрый старт

```bash
cd stars-exchange-bot
cp .env.example .env
# заполните BOT_TOKEN, ADMIN_IDS, ROBOKASSA_*

docker compose up -d --build
```

Локально:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d postgres
alembic upgrade head
python scripts/seed_packages.py
python -m app.main
```

## Robokassa

В личном кабинете Robokassa укажите URL (замените домен на `PUBLIC_BASE_URL`):

| URL | Значение |
|-----|----------|
| Result URL | `https://your-domain/payments/robokassa/result` |
| Success URL | `https://your-domain/payments/robokassa/success` |
| Fail URL | `https://your-domain/payments/robokassa/fail` |

Result URL должен быть доступен из интернета (HTTPS). Метод: GET или POST.

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_IDS` | ID админов через запятую |
| `PUBLIC_BASE_URL` | Публичный URL сервиса |
| `ROBOKASSA_MERCHANT_LOGIN` | Логин магазина |
| `ROBOKASSA_PASSWORD1` | Пароль #1 |
| `ROBOKASSA_PASSWORD2` | Пароль #2 |
| `ROBOKASSA_TEST_MODE` | Тестовый режим (`true`/`false`) |
| `STARS_RUB_RATE` | Курс для произвольной суммы (₽ за 1 ⭐) |
| `STARS_DELIVERY_MODE` | `manual` или `telethon` |
| `TELEGRAM_API_ID` | API ID для Telethon |
| `TELEGRAM_API_HASH` | API Hash для Telethon |
| `TELETHON_SESSION_PATH` | Путь к файлу сессии |

## Telethon (автовыдача)

1. Получите `api_id` / `api_hash` на [my.telegram.org](https://my.telegram.org).
2. Авторизуйте user-сессию (отдельный скрипт или интерактивно):

```bash
python scripts/telethon_login.py
```

3. Установите `STARS_DELIVERY_MODE=telethon`.

На аккаунте-сender должны быть Stars или привязан способ оплаты Telegram для gift-пакетов.

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Меню |
| `/help` | Инструкция |
| `/support` | Поддержка |
| `/admin` | Админ-команды |
| `/admin_orders` | Заказы на выдачу |
| `/admin_fulfill <id>` | Отметить выданным (manual) |

## Тесты

```bash
pytest
```

## Архитектура

```
Bot (aiogram) → Orders (PostgreSQL)
       ↓
Robokassa Result URL → mark paid → Fulfillment
                                      ↓
                            manual / Telethon Stars gift
```
