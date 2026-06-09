# VPN Sales Bot

Telegram-бот для продажи VPN-подписок на базе Amnezia. Оплата через **Telegram Stars**, выдача персональных конфигов, продление и автоотключение по сроку.

## Возможности

- Тарифы: 1 мес / 3 мес (цены в Stars настраиваются в БД)
- Оплата Telegram Stars (встроенные инвойсы, без внешних платёжек)
- Выдача `.vpn` с ключом `vpn://` для приложения **AmneziaVPN**
- Ручная выдача (рекомендуется), SSH-скрипт или amnezia-api
- Пробный период 7 дней (один раз на пользователя)
- Бонус за реферала: +3 дня к подписке
- Напоминания за 7, 3 и 1 день до конца подписки
- Автоотключение просроченных клиентов (при ssh/amnezia_api)

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
| `STARS_BUY_BOT_URL` | Бот для покупки Stars (`https://t.me/StarsFreeRuBot`) |
| `VPN_PROVISIONER` | `manual` / `ssh` / `amnezia_api` |
| `TRIAL_DAYS` | Длительность пробного периода (по умолчанию 7) |
| `REFERRAL_BONUS_DAYS` | Бонус рефереру за первую оплату друга (по умолчанию 3) |

## Telegram Mini App

UI в папке [`../vpn-mini-app/`](../vpn-mini-app/). После деплоя на HTTPS-домен укажите `MINI_APP_URL` в `.env`.

## Telegram Stars

Оплата полностью внутри Telegram — домен и HTTPS для webhooks **не нужны**.

1. В [@BotFather](https://t.me/BotFather) включите платежи для бота (Stars).
2. Пользователь выбирает тариф → получает инвойс → оплачивает Stars.
3. Если Stars не хватает — кнопка «Купить Stars» ведёт в [@StarsFreeRuBot](https://t.me/StarsFreeRuBot).
4. Бот активирует подписку; конфиг выдаёт администратор.

Цены в Stars хранятся в таблице `plans` (`stars_price`):

| Тариф | Stars (по умолчанию) |
|-------|----------------------|
| 1 месяц | 100 |
| 3 месяца | 250 |

Изменить цены:

```sql
UPDATE plans SET stars_price = 100 WHERE code = 'month_1';
UPDATE plans SET is_active = false WHERE code = 'year_1';
```

## Режимы выдачи VPN

### manual (рекомендуется)

Конфиги создаются вручную в **AmneziaVPN** на VPS (Docker Amnezia).

**Процесс для админа после оплаты:**

1. Бот пришлёт уведомление с номером заказа.
2. В AmneziaVPN на сервере: Подключения → ваш сервер → **Поделиться** → **Для приложения AmneziaVPN**.
3. Скопируйте ключ `vpn://...`.
4. В боте: `/admin_approve <order_id>` → вставьте ключ или отправьте файл `.vpn`.

Пользователь получит:
- файл `.vpn` с ключом `vpn://`;
- QR-код для импорта;
- текст ключа для вставки в AmneziaVPN.

**Существующим подписчикам (замена ключа):**

1. `/admin_subscriptions` — найти `telegram_id` пользователя.
2. В AmneziaVPN создать нового клиента → Поделиться → `vpn://`.
3. `/admin_give_config <telegram_id>` → вставить ключ.
4. Пользователь получит новый `.vpn`; старый ключ в БД заменится (новая запись).

```env
VPN_PROVISIONER=manual
```

### ssh (bivlked AWG installer)

На VPS: [bivlked/amneziawg-installer](https://github.com/bivlked/amneziawg-installer).  
Бот вызывает `manage_amneziawg.sh add/remove`, читает конфиг и конвертирует в `vpn://` для AmneziaVPN.

```env
VPN_PROVISIONER=ssh
SSH_HOST=your-vps-ip
SSH_USER=root
SSH_PASSWORD=your-password
SSH_ADD_CLIENT_SCRIPT=/root/awg/manage_amneziawg.sh
SSH_CONFIG_DIR=/root/awg
VPN_SKIP_AWG_ENRICHMENT=true
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
| `/admin` | Все админ-команды (только для ADMIN_IDS) |
| `/stats` | Статистика: пользователи, покупки, Stars, оборот (админ) |
| `/admin_subscriptions` | Сводка: у кого сколько дней осталось (админ) |
| `/admin_orders` | Заказы, ожидающие выдачи (админ) |
| `/admin_approve <id>` | Ручная выдача конфига по заказу (админ) |
| `/admin_give_config <telegram_id>` | Выдать новый уникальный конфиг существующему подписчику (админ) |
| `/admin_vpn_status` | Провижинер и SSH (админ) |
| `/admin_vpn_add [имя]` | Тест: создать клиента на VPS (админ, только ssh) |
| `/admin_vpn_remove [имя]` | Тест: удалить клиента с VPS (админ, только ssh) |
| `/admin_resend_configs` | Разослать сохранённые .vpn всем с активной подпиской (админ) |

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
