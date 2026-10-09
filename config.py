import os
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN", "8801289219:AAGACS4CGXILYeya5B4djcEEo83YDcCuqEc")

# Твой Telegram ID (узнай у @userinfobot и вставь сюда, чтобы работала команда /grant)
ADMIN_ID = 1433139527  

DEFAULT_USER_CONFIG = {
    "min_net_spread": 0.5,
    "amount": 500.0,
    "currency": "RUB",
    "crypto": "USDT",
    "is_active": False,
    # Новые юзеры стартуют без подписки
    "subscription_type": "Нет подписки",
    "expire_date": "Нет",
    "is_vip": False
}

USER_SETTINGS = {}

def get_user_config(user_id: int) -> dict:
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = DEFAULT_USER_CONFIG.copy()
    return USER_SETTINGS[user_id]

def is_user_vip(user_id: int) -> bool:
    cfg = get_user_config(user_id)
    if not cfg.get("is_vip"):
        return False
    exp_str = cfg.get("expire_date")
    if exp_str == "Навсегда":
        return True
    try:
        exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
        if datetime.now() <= exp_dt:
            return True
        else:
            cfg["is_vip"] = False
            cfg["subscription_type"] = "Истекла"
            return False
    except Exception:
        return False
