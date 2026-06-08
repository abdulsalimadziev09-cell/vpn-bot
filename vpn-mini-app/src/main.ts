import "./style.css";
import {
  DOWNLOAD_LINKS,
  FEATURES,
  PLANS,
  REFERRAL_BONUS_DAYS,
  SETUP_STEPS,
  TRIAL_DAYS,
} from "./data";
import { greetingName, initTelegram, sendAction } from "./telegram";

type TabId = "plans" | "features" | "setup";

function renderPlanCard(plan: (typeof PLANS)[number]): string {
  const popularClass = plan.popular ? " popular" : "";
  const badge = plan.badge ? `<span class="plan-badge">${plan.badge}</span>` : "";

  return `
    <article class="plan-card${popularClass}">
      ${badge}
      <div class="plan-head">
        <div>
          <h3 class="plan-title">${plan.title}</h3>
          <p class="plan-days">${plan.days} дней доступа</p>
        </div>
        <div class="plan-price">
          <strong>${plan.starsPrice} ⭐</strong>
          <span>${plan.priceRub} ₽</span>
        </div>
      </div>
      <button class="plan-btn" data-plan-code="${plan.code}">Оплатить в боте</button>
    </article>
  `;
}

function render(): void {
  const name = greetingName();
  const isTelegram = Boolean(initTelegram());

  document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
    ${isTelegram ? "" : '<div class="demo-banner">Откройте через Telegram-бота, чтобы оплатить тариф в один клик.</div>'}

    <section class="hero">
      <div class="hero-glow"></div>
      <div class="brand">
        <div class="brand-icon">🛡️</div>
        <div>
          <p class="brand-title">Nexus VPN</p>
          <p class="brand-subtitle">AmneziaWG · быстро · стабильно</p>
        </div>
      </div>
      <h1>Привет, ${name}!</h1>
      <p>Персональный VPN с выдачей конфига в Telegram. Выберите тариф, подключитесь за пару минут.</p>
      <div class="stats">
        <div class="stat"><strong>150 ⭐</strong><span>от / мес</span></div>
        <div class="stat"><strong>${TRIAL_DAYS} дн.</strong><span>пробный</span></div>
        <div class="stat"><strong>+${REFERRAL_BONUS_DAYS} дн.</strong><span>за друга</span></div>
      </div>
    </section>

    <nav class="tabs" role="tablist">
      <button class="tab active" data-tab="plans" role="tab">Тарифы</button>
      <button class="tab" data-tab="features" role="tab">Плюсы</button>
      <button class="tab" data-tab="setup" role="tab">Настройка</button>
    </nav>

    <section class="panel active" data-panel="plans">
      <h2 class="section-title">Выберите подписку</h2>
      <div class="plans">${PLANS.map(renderPlanCard).join("")}</div>
      <div class="actions">
        <button class="action-btn ghost" data-action="trial">🎁 Пробный период ${TRIAL_DAYS} дней</button>
        <button class="action-btn" data-action="my_subscription">Моя подписка</button>
      </div>
    </section>

    <section class="panel" data-panel="features">
      <h2 class="section-title">Почему Nexus VPN</h2>
      <div class="features">
        ${FEATURES.map(
          (item) => `
            <article class="feature">
              <div class="feature-icon">${item.icon}</div>
              <div>
                <h3>${item.title}</h3>
                <p>${item.text}</p>
              </div>
            </article>
          `,
        ).join("")}
      </div>
      <div class="actions">
        <button class="action-btn primary" data-action="referral">Приведи друга — +${REFERRAL_BONUS_DAYS} дня</button>
      </div>
    </section>

    <section class="panel" data-panel="setup">
      <h2 class="section-title">Как подключиться</h2>
      <ol class="steps">
        ${SETUP_STEPS.map(
          (text, index) => `
            <li class="step">
              <span class="step-num">${index + 1}</span>
              <p>${text}</p>
            </li>
          `,
        ).join("")}
      </ol>
      <div class="downloads">
        <a class="download-link" href="${DOWNLOAD_LINKS.ios}" target="_blank" rel="noopener">📱 iOS</a>
        <a class="download-link" href="${DOWNLOAD_LINKS.android}" target="_blank" rel="noopener">🤖 Android</a>
      </div>
    </section>

    <p class="footer-note">
      Оплата через Telegram Stars. Конфиг и QR приходят в чат с ботом после оплаты.
    </p>
  `;

  bindEvents(isTelegram);
}

function bindEvents(isTelegram: boolean): void {
  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const tabId = tab.dataset.tab as TabId;
      document.querySelectorAll(".tab").forEach((el) => el.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((el) => el.classList.remove("active"));
      tab.classList.add("active");
      document.querySelector(`[data-panel="${tabId}"]`)?.classList.add("active");
    });
  });

  document.querySelectorAll<HTMLButtonElement>("[data-plan-code]").forEach((button) => {
    button.addEventListener("click", () => {
      const planCode = button.dataset.planCode;
      if (!isTelegram || !planCode) {
        return;
      }
      sendAction({ action: "select_plan", plan_code: planCode });
    });
  });

  document.querySelectorAll<HTMLButtonElement>("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!isTelegram) {
        return;
      }
      const action = button.dataset.action;
      if (action === "trial") {
        sendAction({ action: "trial" });
      } else if (action === "my_subscription") {
        sendAction({ action: "my_subscription" });
      } else if (action === "referral") {
        sendAction({ action: "referral" });
      }
    });
  });
}

render();
