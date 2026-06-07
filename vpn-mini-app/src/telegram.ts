export type WebAppAction =
  | { action: "select_plan"; plan_code: string }
  | { action: "trial" }
  | { action: "my_subscription" }
  | { action: "referral" };

type TelegramWebApp = {
  ready: () => void;
  expand: () => void;
  close: () => void;
  sendData: (data: string) => void;
  openLink: (url: string) => void;
  openTelegramLink: (url: string) => void;
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
    setText: (text: string) => void;
    enable: () => void;
    disable: () => void;
  };
  themeParams: Record<string, string | undefined>;
  colorScheme: "light" | "dark";
  initDataUnsafe?: {
    user?: {
      first_name?: string;
      username?: string;
    };
  };
};

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export function getWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function initTelegram(): TelegramWebApp | null {
  const tg = getWebApp();
  if (!tg) {
    return null;
  }

  tg.ready();
  tg.expand();
  document.documentElement.dataset.telegram = "true";
  return tg;
}

export function sendAction(payload: WebAppAction): void {
  const tg = getWebApp();
  if (!tg) {
    console.warn("Telegram WebApp недоступен", payload);
    return;
  }

  tg.sendData(JSON.stringify(payload));
  tg.close();
}

export function greetingName(): string {
  const user = getWebApp()?.initDataUnsafe?.user;
  if (!user?.first_name) {
    return "друг";
  }
  return user.first_name;
}
