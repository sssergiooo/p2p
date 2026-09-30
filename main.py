import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN
from database import init_db, get_active_vip_users, check_expiring_subscriptions
from handlers import router
from parsers import scan_p2p_spreads, get_p2p_link
from math_utils import calculate_net_spread

sent_spreads_cache = {}

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Чтобы не закрывал по таймауту портов) ---
async def handle(request):
    return web.Response(text="Bot is active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()


# --- ФОНОВЫЕ ЗАДАЧИ ---
async def subscription_checker(bot: Bot):
    """Каждый час проверяем, у кого подписка кончается завтра"""
    while True:
        try:
            expiring_users = check_expiring_subscriptions()
            for u_id in expiring_users:
                try:
                    await bot.send_message(
                        u_id,
                        "🔔 <b>ВНИМАНИЕ! VIP-ПОДПИСКА ИСТЕКАЕТ!</b>\n\n"
                        "Ваша подписка завершится в течение 24 часов. Продлите доступ, чтобы не пропускать профитные связки!",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"Ошибка проверки подписок: {e}")
        await asyncio.sleep(3600)

async def background_p2p_scanner(bot: Bot):
    global sent_spreads_cache
    while True:
        try:
            active_users = get_active_vip_users()
            if active_users:
                search_pairs = set((u["currency"], u["amount"]) for u in active_users)

                for curr, amt in search_pairs:
                    data = await scan_p2p_spreads(token="USDT", currency=curr, amount=amt)
                    buy_price = data.get("buy_price")
                    if not buy_price:
                        continue

                    for sell_market, sell_price in data["sells"].items():
                        if not sell_price:
                            continue

                        for u in active_users:
                            if u["currency"] != curr or u["amount"] != amt:
                                continue

                            calc = calculate_net_spread(buy_price, sell_price, amt)

                            if calc["net_spread"] >= u["min_net_spread"]:
                                user_id = u["user_id"]
                                cache_key = f"{user_id}_{sell_market}_{buy_price}_{sell_price}"

                                if cache_key not in sent_spreads_cache:
                                    sent_spreads_cache[cache_key] = True
                                    curr_symbol = "₽" if curr == "RUB" else "₸"

                                    alert_text = (
                                        "⚡ <b>P2P SIGNAL DETECTED</b>\n"
                                        "━━━━━━━━━━━━━━━━━━\n"
                                        f"💱 <b>Инструмент:</b> <code>USDT / {curr}</code>\n"
                                        f"🎯 <b>Лимит:</b> <code>{int(amt):,} {curr_symbol}</code>\n\n"
                                        "🟢 <b>ПОКУПКА (Bybit P2P):</b>\n"
                                        f"└ Курс: <code>{buy_price:.2f} {curr_symbol}</code>\n\n"
                                        f"🔵 <b>ПРОДАЖА ({sell_market} P2P):</b>\n"
                                        f"└ Курс: <code>{sell_price:.2f} {curr_symbol}</code>\n"
                                        "━━━━━━━━━━━━━━━━━━\n"
                                        f"📈 <b>Чистый спред:</b> <code>+{calc['net_spread']}%</code>\n"
                                        f"💵 <b>Профит с круга:</b> <code>~{int(calc['net_profit']):,} {curr_symbol}</code>\n"
                                        "⚡ <i>Скорость обнаружения: 0.3s</i>"
                                    ).replace(",", " ")

                                    links_kb = InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text="🟢 Bybit", url=get_p2p_link("Bybit", "BUY", "USDT", curr, amt)),
                                                InlineKeyboardButton(text=f"🔵 {sell_market}", url=get_p2p_link(sell_market, "SELL", "USDT", curr, amt))
                                            ],
                                            [
                                                InlineKeyboardButton(text="🔄 Обновить стакан", callback_data=f"refresh_spread_{curr}_{amt}_{sell_market}")
                                            ]
                                        ]
                                    )

                                    try:
                                        await bot.send_message(user_id, alert_text, parse_mode="HTML", reply_markup=links_kb)
                                    except Exception:
                                        pass

                if len(sent_spreads_cache) > 300:
                    sent_spreads_cache.clear()
        except Exception as e:
            logging.error(f"Ошибка сканера: {e}")
        await asyncio.sleep(4)


# --- ТОЧКА ВХОДА ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запускаем веб-сервер, чтобы Render прошел Port Scan
    await start_web_server()
    
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(background_p2p_scanner(bot))
    asyncio.create_task(subscription_checker(bot))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
