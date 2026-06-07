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

export const PLANS: Plan[] = [
  {
    id: 1,
    code: "month_1",
    title: "1 месяц",
    days: 30,
    starsPrice: 150,
    priceRub: 299,
  },
  {
    id: 2,
    code: "month_3",
    title: "3 месяца",
    days: 90,
    starsPrice: 400,
    priceRub: 799,
    badge: "−11%",
    popular: true,
  },
  {
    id: 3,
    code: "year_1",
    title: "1 год",
    days: 365,
    starsPrice: 1000,
    priceRub: 2499,
    badge: "Лучшая цена",
  },
];

export const FEATURES = [
  {
    icon: "⚡",
    title: "AmneziaWG",
    text: "Обфускация и стабильное соединение без лишних настроек.",
  },
  {
    icon: "🔐",
    title: "Персональный ключ",
    text: "Один конфиг на пользователя — .conf и QR сразу в Telegram.",
  },
  {
    icon: "🎁",
    title: "Пробный день",
    text: "Попробуйте сервис бесплатно — один раз для новых пользователей.",
  },
  {
    icon: "🌐",
    title: "Туннелирование",
    text: "Бонус: список сайтов для раздельного VPN после подключения.",
  },
];

export const SETUP_STEPS = [
  "Скачайте AmneziaVPN на iOS или Android.",
  "Оплатите тариф в боте — получите .conf и QR.",
  "Импортируйте конфиг в приложение и подключитесь.",
  "Импортируйте amnezia_sites.json для умного туннелирования.",
];

export const DOWNLOAD_LINKS = {
  ios: "https://apps.apple.com/by/app/amneziavpn/id1600529900",
  android: "https://play.google.com/store/apps/details?id=org.amnezia.vpn&hl=ru",
};
