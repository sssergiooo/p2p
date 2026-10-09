import sqlite3
import asyncio
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import Command
from aiocryptopay import AioCryptoPay, Networks
from config import ADMIN_ID, CRYPTO_PAY_TOKEN
from database import get_user, update_user_field, set_user_vip, is_user_vip
from parsers import scan_p2p_spreads
from math_utils import calculate_net_spread

router = Router()

crypto_pay = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    cfg = get_user(user_id)
    has_vip = is_user_vip(user_id)
    
    toggle_text = "🔴 Остановить монитор" if cfg["is_active"] else "🚀 Запустить авто-сканер"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="toggle_monitor")],
            [
                InlineKeyboardButton(text="👤 Мой Профиль", callback_data="show_profile"),
                InlineKeyboardButton(text="⚙️ Фильтры & Лимиты", callback_data="change_limits")
            ],
            [
                InlineKeyboardButton(text="💎 Купить VIP (Crypto / Stars)", callback_data="buy_vip")
            ]
        ]
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    cfg = get_user(user_id)
    has_vip = is_user_vip(user_id)
    curr_symbol = "₽" if cfg["currency"] == "RUB" else "₸"
    
    status_text = f"<code>{cfg['subscription_type']}</code> (до {cfg['expire_date']})" if has_vip else "❌ <code>Нет подписки</code>"

    text = (
        "🔥 <b>P2P ARBITRAGE TERMINAL v2.0</b>\n"
        "━━━━━━━★━━━━━━━\n\n"
        "Профессиональный сканер межбиржевых связок!\n\n"
        "📍 <b>Текущие настройки поиска:</b>\n"
        f"├ Валюта: <code>{cfg['currency']}</code>\n"
        f"├ Лимит ордера: <code>{int(cfg['amount']):,} {curr_symbol}</code>\n"
        f"├ Мин. спред: <code>≥ {cfg['min_net_spread']}%</code>\n"
        f"├ Способ оплаты: <code>{cfg['payment_method']}</code>\n"
        f"└ Мин. сделок продавца: <code>{cfg['min_orders']}</code>\n\n"
        f"🔑 <b>Статус доступа:</b> {status_text}\n\n"
        "<i>Для запуска мониторинга необходима активная VIP-подписка.</i>"
    ).replace(",", " ")
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

@router.callback_query(F.data == "show_profile")
async def show_profile(call: CallbackQuery):
    user_id = call.from_user.id
    cfg = get_user(user_id)
    has_vip = is_user_vip(user_id)
    curr_symbol = "₽" if cfg["currency"] == "RUB" else "₸"

    status_str = f"✅ {cfg['subscription_type']}" if has_vip else "❌ Не активна"

    text = (
        "👤 <b>ЛИЧНЫЙ КАБИНЕТ ПОЛЬЗОВАТЕЛЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👑 VIP-Статус: <b>{status_str}</b>\n"
        f"⏳ Срок действия: <code>{cfg['expire_date']}</code>\n\n"
        "📊 <b>Рабочие фильтры:</b>\n"
        f"├ Валюта: <b>{cfg['currency']}</b>\n"
        f"├ Объём круга: <b>{int(cfg['amount']):,} {curr_symbol}</b>\n"
        f"├ Порог спреда: <b>≥ {cfg['min_net_spread']}%</b>\n"
        f"├ Способ оплаты: <b>{cfg['payment_method']}</b>\n"
        f"└ Мин. сделок мерчанта: <b>{cfg['min_orders']}</b>\n"
    ).replace(",", " ")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить / Продлить VIP", callback_data="buy_vip")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_main")]
        ]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "back_main")
async def back_to_main(call: CallbackQuery):
    user_id = call.from_user.id
    cfg = get_user(user_id)
    has_vip = is_user_vip(user_id)
    curr_symbol = "₽" if cfg["currency"] == "RUB" else "₸"

    status_text = f"<code>{cfg['subscription_type']}</code> (до {cfg['expire_date']})" if has_vip else "❌ <code>Нет подписки</code>"

    text = (
        "🔥 <b>P2P ARBITRAGE TERMINAL v2.0</b>\n"
        "━━━━━━━★━━━━━━━\n\n"
        "Профессиональный сканер межбиржевых связок!\n\n"
        "📍 <b>Текущие настройки поиска:</b>\n"
        f"├ Валюта: <code>{cfg['currency']}</code>\n"
        f"├ Лимит ордера: <code>{int(cfg['amount']):,} {curr_symbol}</code>\n"
        f"├ Мин. спред: <code>≥ {cfg['min_net_spread']}%</code>\n"
        f"├ Способ оплаты: <code>{cfg['payment_method']}</code>\n"
        f"└ Мин. сделок продавца: <code>{cfg['min_orders']}</code>\n\n"
        f"🔑 <b>Статус доступа:</b> {status_text}\n\n"
        "<i>Для запуска мониторинга необходима активная VIP-подписка.</i>"
    ).replace(",", " ")
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

@router.callback_query(F.data == "toggle_monitor")
async def toggle_monitor(call: CallbackQuery):
    user_id = call.from_user.id
    cfg = get_user(user_id)

    if not is_user_vip(user_id):
        await call.answer("❌ Доступ ограничен! Приобретите VIP-подписку.", show_alert=True)
        return

    new_status = not cfg["is_active"]
    update_user_field(user_id, "is_active", 1 if new_status else 0)
    
    status_str = "запущен 🟢" if new_status else "остановлен 🔴"
    await call.answer(f"Авто-сканер {status_str}", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=get_main_keyboard(user_id))

@router.callback_query(F.data == "change_limits")
async def show_limit_options(call: CallbackQuery):
    cfg = get_user(call.from_user.id)
    curr = cfg["currency"]
    curr_symbol = "₽" if curr == "RUB" else "₸"

    bank_buttons = [
        InlineKeyboardButton(text="🏦 Сбербанк", callback_data="set_bank_Sberbank"),
        InlineKeyboardButton(text="🏦 Т-Банк (Tinkoff)", callback_data="set_bank_Tinkoff")
    ] if curr == "RUB" else [
        InlineKeyboardButton(text="🏦 Kaspi Bank", callback_data="set_bank_Kaspi"),
        InlineKeyboardButton(text="🏦 Halyk Bank", callback_data="set_bank_Halyk")
    ]

    amount_buttons_row1 = [
        InlineKeyboardButton(text="💰 500 ₽", callback_data="set_amount_500"),
        InlineKeyboardButton(text="💰 5k ₽", callback_data="set_amount_5000"),
        InlineKeyboardButton(text="💰 15k ₽", callback_data="set_amount_15000")
    ] if curr == "RUB" else [
        InlineKeyboardButton(text="💰 900 ₸", callback_data="set_amount_900"),
        InlineKeyboardButton(text="💰 10k ₸", callback_data="set_amount_10000"),
        InlineKeyboardButton(text="💰 50k ₸", callback_data="set_amount_50000")
    ]

    amount_buttons_row2 = [
        InlineKeyboardButton(text="💰 50k ₽", callback_data="set_amount_50000"),
        InlineKeyboardButton(text="💰 100k ₽", callback_data="set_amount_100000")
    ] if curr == "RUB" else [
        InlineKeyboardButton(text="💰 250k ₸", callback_data="set_amount_250000"),
        InlineKeyboardButton(text="💰 500k ₸", callback_data="set_amount_500000")
    ]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 RUB (Рубли)", callback_data="set_curr_RUB"),
                InlineKeyboardButton(text="🇰🇿 KZT (Тенге)", callback_data="set_curr_KZT")
            ],
            amount_buttons_row1,
            amount_buttons_row2,
            bank_buttons,
            [
                InlineKeyboardButton(text="🌐 Все банки (ALL)", callback_data="set_bank_ALL")
            ],
            [
                InlineKeyboardButton(text="🎯 Спред 0.3%", callback_data="set_spread_0.3"),
                InlineKeyboardButton(text="🎯 Спред 0.5%", callback_data="set_spread_0.5"),
                InlineKeyboardButton(text="🎯 Спред 1.0%", callback_data="set_spread_1.0")
            ],
            [
                InlineKeyboardButton(text="📊 От 5 ордеров", callback_data="set_orders_5"),
                InlineKeyboardButton(text="📊 От 20 ордеров", callback_data="set_orders_20")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
        ]
    )

    text = (
        "⚙️ <b>НАСТРОЙКА ФИЛЬТРОВ И ЛИМИТОВ:</b>\n\n"
        f"Валюта: <b>{cfg['currency']}</b>\n"
        f"Лимит ордера: <b>{int(cfg['amount']):,} {curr_symbol}</b>\n"
        f"Текущий банк: <b>{cfg['payment_method']}</b>\n"
        f"Мин. спред: <b>≥ {cfg['min_net_spread']}%</b>\n"
        f"Мин. ордеров продавца: <b>{cfg['min_orders']}</b>"
    ).replace(",", " ")

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("set_curr_"))
async def set_currency(call: CallbackQuery):
    curr = call.data.split("_")[2]
    update_user_field(call.from_user.id, "currency", curr)
    default_amount = 500.0 if curr == "RUB" else 900.0
    update_user_field(call.from_user.id, "amount", default_amount)
    await call.answer(f"Валюта изменена на {curr}", show_alert=True)
    await show_limit_options(call)

@router.callback_query(F.data.startswith("set_amount_"))
async def set_amount(call: CallbackQuery):
    amt = float(call.data.split("_")[2])
    update_user_field(call.from_user.id, "amount", amt)
    cfg = get_user(call.from_user.id)
    curr_symbol = "₽" if cfg["currency"] == "RUB" else "₸"
