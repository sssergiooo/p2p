import asyncio
import logging
import aiohttp

# Универсальные заголовки браузера
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json"
}

# 🟢 ЗАКУПКА: BYBIT P2P
async def fetch_bybit_buy(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    url = "https://api2.bybit.com/fiat/otc/item/online"
    headers = {**BASE_HEADERS, "Origin": "https://www.bybit.com", "Referer": "https://www.bybit.com/"}
    payload = {
        "userId": "",
        "tokenId": token,
        "currencyId": currency,
        "payment": [],
        "side": "1",  # 1 = Buy USDT (Закуп)
        "size": "10",
        "page": "1",
        "amount": str(amount) if amount else ""
    }
    try:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("result", {}).get("items", [])
                if items:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"Bybit Buy error: {e}")
    return 0.0

# 🟢 ЗАКУПКА: HTX P2P (РЕЗЕРВ)
async def fetch_htx_buy(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    curr_id = 11 if currency == "RUB" else 62
    url = f"https://otc-api.ecloud.host/v1/otc/trade/list/public?coinId=2&currency={curr_id}&tradeType=sell&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount={amount}"
    headers = {**BASE_HEADERS, "Origin": "https://c2c.htx.com", "Referer": "https://c2c.htx.com/"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", [])
                if items and len(items) > 0:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"HTX Buy error: {e}")
    return 0.0

# 🔵 ПРОДАЖА: BINGX P2P
async def fetch_bingx_sell(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    # side=BUY означает, что мы продаём мейкеру, который покупает
    url = f"https://open-api.bingx.com/openApi/otc/v1/merchant/goods?fiat={currency}&crypto={token}&side=BUY&amount={amount}"
    headers = {**BASE_HEADERS, "Referer": "https://bingx.com/"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", {}).get("goods", [])
                if items:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"BingX Sell error: {e}")
    return 0.0

# 🔵 ПРОДАЖА: HTX P2P
async def fetch_htx_sell(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    curr_id = 11 if currency == "RUB" else 62
    # tradeType=buy означают объявления покупателей
    url = f"https://otc-api.ecloud.host/v1/otc/trade/list/public?coinId=2&currency={curr_id}&tradeType=buy&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount={amount}"
    headers = {**BASE_HEADERS, "Origin": "https://c2c.htx.com", "Referer": "https://c2c.htx.com/"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", [])
                if items and len(items) > 0:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"HTX Sell error: {e}")
    return 0.0

# 🔵 ПРОДАЖА: MEXC P2P
async def fetch_mexc_sell(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    url = f"https://www.mexc.com/api/platform/p2p/api/v1/trade/list?coin={token}&currency={currency}&tradeType=BUY&page=1&limit=10&amount={amount}"
    headers = {**BASE_HEADERS, "Origin": "https://www.mexc.com", "Referer": "https://www.mexc.com/p2p"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", [])
                if items and len(items) > 0:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"MEXC Sell error: {e}")
    return 0.0

# 🔵 ПРОДАЖА: BITGET P2P
async def fetch_bitget_sell(session: aiohttp.ClientSession, token="USDT", currency="RUB", amount=500.0) -> float:
    url = "https://www.bitget.com/v1/p2p/pub/adv/list"
    headers = {**BASE_HEADERS, "Origin": "https://www.bitget.com", "Referer": "https://www.bitget.com/p2p-trade"}
    payload = {
        "coin": token,
        "fiat": currency,
        "side": "BUY",
        "pageNo": 1,
        "pageSize": 10,
        "amount": str(amount) if amount else ""
    }
    try:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", {}).get("advList", [])
                if items:
                    return float(items[0]["price"])
    except Exception as e:
        logging.error(f"Bitget Sell error: {e}")
    return 0.0

# ПАРАЛЛЕЛЬНОЕ СКАНИРОВАНИЕ ВСЕХ БИРЖ
async def scan_p2p_spreads(token="USDT", currency="RUB", amount=500.0) -> dict:
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            fetch_bybit_buy(session, token, currency, amount),
            fetch_htx_buy(session, token, currency, amount),
            fetch_bingx_sell(session, token, currency, amount),
            fetch_htx_sell(session, token, currency, amount),
            fetch_mexc_sell(session, token, currency, amount),
            fetch_bitget_sell(session, token, currency, amount),
            return_exceptions=True
        )
    
    bybit_b = results[0] if isinstance(results[0], (int, float)) else 0.0
    htx_b = results[1] if isinstance(results[1], (int, float)) else 0.0
    bingx_s = results[2] if isinstance(results[2], (int, float)) else 0.0
    htx_s = results[3] if isinstance(results[3], (int, float)) else 0.0
    mexc_s = results[4] if isinstance(results[4], (int, float)) else 0.0
    bitget_s = results[5] if isinstance(results[5], (int, float)) else 0.0

    buy_price = bybit_b if bybit_b > 0 else htx_b
    buy_market = "Bybit" if bybit_b > 0 else ("HTX" if htx_b > 0 else "None")

    return {
        "buy_price": buy_price,
        "buy_market": buy_market,
        "sells": {
            "BingX": bingx_s,
            "HTX": htx_s,
            "MEXC": mexc_s,
            "Bitget": bitget_s
        }
    }

def get_p2p_link(market: str, side: str, token: str, currency: str, amount: float) -> str:
    if market == "Bybit":
        return f"https://www.bybit.com/fiat/trade/otc/?actionType=1&token={token}&fiat={currency}"
    elif market == "BingX":
        return "https://bingx.com/en-us/p2p/"
    elif market == "HTX":
        return "https://c2c.htx.com/fiat-crypto/trade"
    elif market == "MEXC":
        return "https://www.mexc.com/p2p"
    elif market == "Bitget":
        return "https://www.bitget.com/p2p-trade"
    return "https://t.me"
