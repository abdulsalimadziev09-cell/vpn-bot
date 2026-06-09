export const TRIAL_DAYS = 7;
export const REFERRAL_BONUS_DAYS = 3;
export const STARS_BUY_BOT_URL = "https://t.me/StarsFreeRuBot";

export type Plan = {
  id: number;
  code: string;
  title: string;
  days: number;
  starsPrice: number;
  priceRub: number;
  badge?: string;
  popular?: boolean;
};

/** Синхронизировано с plans в БД бота (alembic 006). */
export const PLANS: Plan[] = [
  {
    id: 1,
    code: "month_1",
    title: "1 месяц",
    days: 30,
    starsPrice: 100,
    priceRub: 299,
  },
  {
    id: 2,
    code: "month_3",
    title: "3 месяца",
    days: 90,
    starsPrice: 250,
    priceRub: 799,
    badge: "−17%",
    popular: true,
  },
];

export const FEATURES = [
  {
    icon: "🛡️",
    title: "Amnezia VPN",
    text: "Персональный VPN с обфускацией — стабильное соединение без лишних настроек.",
  },
  {
    icon: "🔐",
    title: "Один ключ — один пользователь",
    text: "Персональный конфиг: файл .vpn с ключом vpn:// в чате с ботом.",
  },
  {
    icon: "⭐",
    title: "Оплата Telegram Stars",
    text: "Инвойс прямо в боте. Не хватает Stars — пополните через @StarsFreeRuBot.",
  },
  {
    icon: "⏳",
    title: "Напоминания",
    text: "Бот напомнит за 7, 3 и 1 день до окончания подписки.",
  },
  {
    icon: "🎁",
    title: "Пробный период",
    text: `${TRIAL_DAYS} дней бесплатно — один раз для новых пользователей.`,
  },
  {
    icon: "👥",
    title: "Приведи друга",
    text: `+${REFERRAL_BONUS_DAYS} дня к подписке, когда друг впервые оплатит тариф.`,
  },
];

export const SETUP_STEPS = [
  "Скачайте AmneziaVPN на iOS, Android или компьютер (ссылки ниже).",
  "Выберите тариф в приложении или в боте и оплатите Stars.",
  "После оплаты администратор выдаст файл .vpn с ключом vpn:// — обычно в течение нескольких минут.",
  "В AmneziaVPN: «Добавить VPN» → импортируйте .vpn или вставьте ключ vpn://.",
  "Подключитесь к VPN. Повторно получить конфиг: /my → «Получить конфиг».",
];

export const DOWNLOAD_LINKS = {
  ios: "https://apps.apple.com/app/amneziavpn/id1600529900",
  android: "https://play.google.com/store/apps/details?id=org.amnezia.vpn&hl=ru",
  desktop: "https://amnezia.org",
};

export function minStarsPrice(): number {
  return Math.min(...PLANS.map((plan) => plan.starsPrice));
}
