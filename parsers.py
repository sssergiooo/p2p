import aiohttp
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 🟢 ЗАКУПКА СТРОГО НА BYBIT P2P
async def fetch_bybit_buy(token="USDT", currency="RUB", amount=500.0) -> float:
    url = "https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "userId": "",
        "tokenId": token,
        "currencyId": currency,
        "payment": [],
        "side": "1",  # 1 = BUY (закуп)
        "size": "10",
        "page": "1",
        "amount": str(amount) if amount else ""
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("result", {}).get("items", [])
                    if items:
                        return float(items[0]["price"])
    except Exception as e:
        logging.error(f"Bybit Buy parser error: {e}")
    return 0.0

# 🔵 ПРОДАЖА НА BINGX
async def fetch_bingx_sell(token="USDT", currency="RUB", amount=500.0) -> float:
    url = f"https://open-api.bingx.com/openApi/otc/v1/merchant/goods?fiat={currency}&crypto={token}&side=SELL&amount={amount}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", {}).get("goods", [])
                    if items:
                        return float(items[0]["price"])
    except Exception as e:
        logging.error(f"BingX Sell parser error: {e}")
    return 0.0

# 🔵 ПРОДАЖА НА HTX (HUOBI)
async def fetch_htx_sell(token="USDT", currency="RUB", amount=500.0) -> float:
    curr_id = 11 if currency == "RUB" else 62
    endpoints = [
        f"https://otc-api.htx.com/v1/otc/trade/list/public?coinId=2&currency={curr_id}&tradeType=sell&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount={amount}",
        f"https://otc-api.ecloud.host/v1/otc/trade/list/public?coinId=2&currency={curr_id}&tradeType=sell&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount={amount}"
    ]
    for url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, timeout=7) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("data", [])
                        if items and len(items) > 0:
                            return float(items[0]["price"])
        except Exception as e:
            logging.error(f"HTX Sell parser error ({url}): {e}")
    return 0.0

# 🔵 ПРОДАЖА НА MEXC
async def fetch_mexc_sell(token="USDT", currency="RUB", amount=500.0) -> float:
    url = f"https://www.mexc.com/api/platform/p2p/api/v1/trade/list?coin={token}&currency={currency}&tradeType=SELL&page=1&limit=10&amount={amount}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", [])
                    if items and len(items) > 0:
                        return float(items[0]["price"])
    except Exception as e:
        logging.error(f"MEXC Sell parser error: {e}")
    return 0.0

# 🔵 ПРОДАЖА НА BITGET
async def fetch_bitget_sell(token="USDT", currency="RUB", amount=500.0) -> float:
    url = "https://www.bitget.com/v1/p2p/pub/adv/list"
    payload = {
        "coin": token,
        "fiat": currency,
        "side": "SELL",
        "pageNo": 1,
        "pageSize": 10,
        "amount": str(amount) if amount else ""
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("data", {}).get("advList", [])
                    if items:
                        return float(items[0]["price"])
    except Exception as e:
        logging.error(f"Bitget Sell parser error: {e}")
    return 0.0

# СКАНИРОВАНИЕ: ЗАКУП BYBIT ➔ ПРОДАЖА НА ВСЕХ БИРЖАХ
async def scan_p2p_spreads(token="USDT", currency="RUB", amount=500.0) -> dict:
    buy_p = await fetch_bybit_buy(token, currency, amount)
    
    bingx_s = await fetch_bingx_sell(token, currency, amount)
    htx_s = await fetch_htx_sell(token, currency, amount)
    mexc_s = await fetch_mexc_sell(token, currency, amount)
    bitget_s = await fetch_bitget_sell(token, currency, amount)
    
    return {
        "buy_price": buy_p,
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
