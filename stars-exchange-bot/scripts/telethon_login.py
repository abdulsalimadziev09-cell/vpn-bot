"""One-time Telethon login to create operator session."""

import asyncio
import getpass

from telethon import TelegramClient

from app.config import settings


async def main() -> None:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")

    client = TelegramClient(
        settings.telethon_session_path,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.connect()
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Already authorized as @{me.username or me.id}")
        await client.disconnect()
        return

    phone = input("Phone (+7...): ").strip()
    await client.send_code_request(phone)
    code = input("Code from Telegram: ").strip()
    try:
        await client.sign_in(phone, code)
    except Exception:
        password = getpass.getpass("2FA password: ")
        await client.sign_in(password=password)

    me = await client.get_me()
    print(f"Logged in as @{me.username or me.id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
