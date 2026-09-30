import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from config import ADMIN_ID

# Читаем ссылку подключения из Environment Variables Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Создает и возвращает новое подключение к PostgreSQL в Supabase"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Создание таблицы пользователей в Supabase при старте бота"""
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL не найден в Environment Variables!")
        return

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    min_net_spread REAL DEFAULT 0.5,
                    amount REAL DEFAULT 500.0,
                    currency TEXT DEFAULT 'RUB',
                    is_active INT DEFAULT 0,
                    subscription_type TEXT DEFAULT 'Нет подписки',
                    expire_date TEXT DEFAULT 'Нет',
                    is_vip INT DEFAULT 0,
                    payment_method TEXT DEFAULT 'ALL',
                    min_orders INT DEFAULT 10,
                    notified_before_exp INT DEFAULT 0
                );
            """)

def get_user(user_id: int) -> dict:
    is_admin = (user_id == ADMIN_ID and ADMIN_ID != 0)

    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT min_net_spread, amount, currency, is_active, subscription_type, 
                       expire_date, is_vip, payment_method, min_orders 
                FROM users WHERE user_id = %s
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                default_vip = 1 if is_admin else 0
                default_sub = "VIP Навсегда" if is_admin else "Нет подписки"
                default_exp = "Навсегда" if is_admin else "Нет"

                cursor.execute("""
                    INSERT INTO users (user_id, is_vip, subscription_type, expire_date) 
                    VALUES (%s, %s, %s, %s)
                """, (user_id, default_vip, default_sub, default_exp))
                
                return {
                    "min_net_spread": 0.5,
                    "amount": 500.0,
                    "currency": "RUB",
                    "is_active": False,
                    "subscription_type": default_sub,
                    "expire_date": default_exp,
                    "is_vip": is_admin,
                    "payment_method": "ALL",
                    "min_orders": 10
                }

            if is_admin and not bool(row["is_vip"]):
                cursor.execute("""
                    UPDATE users 
                    SET is_vip = 1, subscription_type = 'VIP Навсегда', expire_date = 'Навсегда' 
                    WHERE user_id = %s
                """, (user_id,))
                row["is_vip"] = 1
                row["subscription_type"] = "VIP Навсегда"
                row["expire_date"] = "Навсегда"

    return {
        "min_net_spread": row["min_net_spread"],
        "amount": row["amount"],
        "currency": row["currency"],
        "is_active": bool(row["is_active"]),
        "subscription_type": row["subscription_type"],
        "expire_date": row["expire_date"],
        "is_vip": bool(row["is_vip"]),
        "payment_method": row["payment_method"] if row["payment_method"] else "ALL",
        "min_orders": row["min_orders"] if row["min_orders"] is not None else 10
    }

def update_user_field(user_id: int, field: str, value):
    # Безопасная фильтрация названий полей
    allowed_fields = [
        "min_net_spread", "amount", "currency", "is_active", 
        "subscription_type", "expire_date", "is_vip", 
        "payment_method", "min_orders", "notified_before_exp"
    ]
    if field not in allowed_fields:
        return

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE users SET {field} = %s WHERE user_id = %s", (value, user_id))

def set_user_vip(user_id: int, days: int):
    if days >= 3650:
        sub_type = "VIP Навсегда"
        exp_date = "Навсегда"
    else:
        sub_type = f"VIP {days}дн"
        exp_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET is_vip = 1, subscription_type = %s, expire_date = %s, notified_before_exp = 0 
                WHERE user_id = %s
            """, (sub_type, exp_date, user_id))

def is_user_vip(user_id: int) -> bool:
    user = get_user(user_id)
    if not user["is_vip"]:
        return False
    if user["expire_date"] == "Навсегда":
        return True
    try:
        exp_dt = datetime.strptime(user["expire_date"], "%Y-%m-%d")
        if datetime.now() <= exp_dt:
            return True
        else:
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET is_vip = 0, subscription_type = 'Истекла' WHERE user_id = %s", (user_id,))
            return False
    except Exception:
        return False

def get_active_vip_users():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT user_id, currency, amount, min_net_spread, payment_method, min_orders 
                FROM users WHERE is_active = 1 AND is_vip = 1
            """)
            rows = cursor.fetchall()

    return [{
        "user_id": r["user_id"], 
        "currency": r["currency"], 
        "amount": r["amount"], 
        "min_net_spread": r["min_net_spread"], 
        "payment_method": r["payment_method"], 
        "min_orders": r["min_orders"]
    } for r in rows]

def check_expiring_subscriptions():
    """Возвращает юзеров, у которых подписка кончается завтра"""
    expiring_soon = []
    now = datetime.now()

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, expire_date 
                FROM users 
                WHERE is_vip = 1 AND notified_before_exp = 0 AND expire_date != 'Навсегда'
            """)
            rows = cursor.fetchall()

            for u_id, exp_str in rows:
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                    diff = (exp_dt - now).total_seconds()
                    if 0 < diff <= 86400:  # Осталось менее 24 часов
                        expiring_soon.append(u_id)
                        cursor.execute("UPDATE users SET notified_before_exp = 1 WHERE user_id = %s", (u_id,))
                except Exception:
                    pass

    return expiring_soon
