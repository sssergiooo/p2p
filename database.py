import sqlite3
from datetime import datetime, timedelta
from config import ADMIN_ID

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            min_net_spread REAL DEFAULT 0.1,
            amount REAL DEFAULT 5000.0,
            currency TEXT DEFAULT 'RUB',
            is_active INTEGER DEFAULT 1,
            subscription_type TEXT DEFAULT 'VIP Навсегда',
            expire_date TEXT DEFAULT 'Навсегда',
            is_vip INTEGER DEFAULT 1,
            payment_method TEXT DEFAULT 'ALL',
            min_orders INTEGER DEFAULT 10,
            notified_before_exp INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: int) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT min_net_spread, amount, currency, is_active, subscription_type, 
               expire_date, is_vip, payment_method, min_orders 
        FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    
    is_admin = (user_id == ADMIN_ID and ADMIN_ID != 0)

    if not row:
        cursor.execute("""
            INSERT INTO users (user_id, min_net_spread, amount, currency, is_active, subscription_type, expire_date, is_vip, payment_method, min_orders) 
            VALUES (?, 0.1, 5000.0, 'RUB', 1, 'VIP Навсегда', 'Навсегда', 1, 'ALL', 10)
        """, (user_id,))
        conn.commit()
        conn.close()
        return {
            "user_id": user_id,
            "min_net_spread": 0.1,
            "amount": 5000.0,
            "currency": "RUB",
            "is_active": True,
            "subscription_type": "VIP Навсегда",
            "expire_date": "Навсегда",
            "is_vip": True,
            "payment_method": "ALL",
            "min_orders": 10
        }

    conn.close()
    return {
        "user_id": user_id,
        "min_net_spread": float(row[0]),
        "amount": float(row[1]),
        "currency": str(row[2]),
        "is_active": True if is_admin else bool(row[3]),
        "subscription_type": "VIP Навсегда" if is_admin else str(row[4]),
        "expire_date": "Навсегда" if is_admin else str(row[5]),
        "is_vip": True if is_admin else bool(row[6]),
        "payment_method": str(row[7]) if row[7] else "ALL",
        "min_orders": int(row[8]) if row[8] is not None else 10
    }

def update_user_field(user_id: int, field: str, value):
    get_user(user_id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def set_user_vip(user_id: int, days: int):
    get_user(user_id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET is_vip = 1, subscription_type = 'VIP Навсегда', expire_date = 'Навсегда', is_active = 1 
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def is_user_vip(user_id: int) -> bool:
    return True

def get_active_vip_users():
    # ЖЕСТКИЙ АВТО-ВОЗВРАТ ДЛЯ АДМИНА (ИГНОРИРУЕТ ВСЕ СБОИ БАЗЫ)
    admin_cfg = get_user(ADMIN_ID)
    return [{
        "user_id": ADMIN_ID,
        "currency": admin_cfg["currency"],
        "amount": admin_cfg["amount"],
        "min_net_spread": admin_cfg["min_net_spread"],
        "payment_method": admin_cfg["payment_method"],
        "min_orders": admin_cfg["min_orders"]
    }]

def check_expiring_subscriptions():
    return []
