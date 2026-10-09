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
            amount REAL DEFAULT 500.0,
            currency TEXT DEFAULT 'RUB',
            is_active INTEGER DEFAULT 0,
            subscription_type TEXT DEFAULT 'Нет подписки',
            expire_date TEXT DEFAULT 'Нет',
            is_vip INTEGER DEFAULT 0,
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
        default_vip = 1 if is_admin else 0
        default_sub = "VIP Навсегда" if is_admin else "Нет подписки"
        default_exp = "Навсегда" if is_admin else "Нет"

        cursor.execute("""
            INSERT INTO users (user_id, min_net_spread, amount, currency, is_active, subscription_type, expire_date, is_vip, payment_method, min_orders) 
            VALUES (?, 0.1, 500.0, 'RUB', 0, ?, ?, ?, 'ALL', 10)
        """, (user_id, default_sub, default_exp, default_vip))
        conn.commit()
        conn.close()
        return {
            "user_id": user_id,
            "min_net_spread": 0.1,
            "amount": 500.0,
            "currency": "RUB",
            "is_active": False,
            "subscription_type": default_sub,
            "expire_date": default_exp,
            "is_vip": is_admin,
            "payment_method": "ALL",
            "min_orders": 10
        }

    if is_admin and (row[6] == 0 or row[4] != "VIP Навсегда"):
        cursor.execute("UPDATE users SET is_vip = 1, subscription_type = 'VIP Навсегда', expire_date = 'Навсегда' WHERE user_id = ?", (user_id,))
        conn.commit()
        cursor.execute("""
            SELECT min_net_spread, amount, currency, is_active, subscription_type, 
                   expire_date, is_vip, payment_method, min_orders 
            FROM users WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()

    conn.close()
    return {
        "user_id": user_id,
        "min_net_spread": float(row[0]),
        "amount": float(row[1]),
        "currency": str(row[2]),
        "is_active": bool(row[3]),
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
    if days >= 3650:
        sub_type = "VIP Навсегда"
        exp_date = "Навсегда"
    else:
        sub_type = f"VIP {days}дн"
        exp_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    cursor.execute("""
        UPDATE users 
        SET is_vip = 1, subscription_type = ?, expire_date = ?, notified_before_exp = 0 
        WHERE user_id = ?
    """, (sub_type, exp_date, user_id))
    conn.commit()
    conn.close()

def is_user_vip(user_id: int) -> bool:
    if user_id == ADMIN_ID and ADMIN_ID != 0:
        return True
    user = get_user(user_id)
    return bool(user["is_vip"])

def get_active_vip_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_vip = 1, subscription_type = 'VIP Навсегда', expire_date = 'Навсегда' WHERE user_id = ?", (ADMIN_ID,))
    conn.commit()

    cursor.execute("""
        SELECT user_id, currency, amount, min_net_spread, payment_method, min_orders 
        FROM users WHERE is_active = 1 AND is_vip = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{
        "user_id": r[0], "currency": r[1], "amount": float(r[2]), 
        "min_net_spread": float(r[3]), "payment_method": r[4], "min_orders": int(r[5])
    } for r in rows]

def check_expiring_subscriptions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expire_date FROM users WHERE is_vip = 1 AND notified_before_exp = 0 AND expire_date != 'Навсегда'")
    rows = cursor.fetchall()
    
    expiring_soon = []
    now = datetime.now()
    
    for u_id, exp_str in rows:
        try:
            exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
            diff = (exp_dt - now).total_seconds()
            if 0 < diff <= 86400:
                expiring_soon.append(u_id)
                cursor.execute("UPDATE users SET notified_before_exp = 1 WHERE user_id = ?", (u_id,))
        except Exception:
            pass
            
    conn.commit()
    conn.close()
    return expiring_soon
