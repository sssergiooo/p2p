import aiohttp
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_p2p_link(exchange: str, trade_type: str = "BUY", crypto: str = "USDT", currency: str = "RUB", amount: float = 5000.0) -> str:
    amount_str = str(int(amount))
    
    if exchange == "Bybit":
        action_type = "1" if trade_type.upper() == "BUY" else "0"
        return f"https://www.bybit.com/fiat/trade/otc/?actionType={action_type}&token={crypto}&fiat={currency}&amount={amount_str}"
    
    elif exchange == "BingX":
        return f"https://bingx.com/ru-ru/p2p/"
    
    elif exchange == "HTX":
        return f"https://www.htx.com/ru-ru/fiat-crypto/trader/"

    elif exchange == "Gate":
        return f"https://www.gate.io/ru/c2c/market"

    return "https://t.me"

# 1. Покупка на Bybit P2P
async def get_bybit_p2p_price(side: str = "1", token: str = "USDT", currency: str = "RUB", amount: float = 5000.0) -> float | None:
    url = "https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "tokenId": token,
        "currencyId": currency,
        "side": str(side), # 1 = BUY, 0 = SELL
        "size": "10",
        "page": "1",
        "amount": str(amount)
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("result", {}).get("items", [])
                    if items:
                        return float(items[0]["price"])
    except Exception as e:
        logging.error(f"Ошибка Bybit P2P: {e}")
    return None

# 2. Продажа на BingX P2P
async def get_bingx_p2p_price(trade_type: str = "SELL", crypto: str = "USDT", fiat: str = "RUB", amount: float = 5000.0) -> float | None:
    url = "https://open-api.bingx.com/openApi/p2p/v1/merchant/ad/list"
    side = "2" if trade_type.upper() == "SELL" else "1"
    params = {
        "crypto": crypto,
        "fiat": fiat,
        "side": side,
        "amount": str(amount),
        "page": 1,
        "pageSize": 10
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=HEADERS, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ads = data.get("data", {}).get("ads", [])
                    if ads:
                        return float(ads[0]["price"])
    except Exception as e:
        logging.error(f"Ошибка BingX P2P: {e}")
    return None

# 3. Продажа на HTX (Huobi) P2P
async def get_htx_p2p_price(trade_type: str = "SELL", crypto: str = "USDT", fiat: str = "RUB", amount: float = 5000.0) -> float | None:
    url = f"https://otc-api.htx.com/v1/otc/trade/list/public?coinId=2&currency={currency_to_htx(fiat)}&tradeType={trade_type.lower()}&currPage=1&payMethod=0&acceptOrder=-1&country=0&blockType=general&online=1&range=0&amount={amount}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ads = data.get("data", [])
                    if ads:
                        return float(ads[0]["price"])
    except Exception as e:
        logging.error(f"Ошибка HTX P2P: {e}")
    return None

def currency_to_htx(curr: str) -> int:
    # Идентификаторы валют в HTX API
    mapping = {"RUB": 11, "KZT": 14}
    return mapping.get(curr, 11)

async def scan_p2p_spreads(token: str = "USDT", currency: str = "RUB", amount: float = 5000.0) -> dict:
    bybit_buy = await get_bybit_p2p_price(side="1", token=token, currency=currency, amount=amount)
    
    bingx_sell = await get_bingx_p2p_price(trade_type="SELL", crypto=token, fiat=currency, amount=amount)
    htx_sell = await get_htx_p2p_price(trade_type="SELL", crypto=token, fiat=currency, amount=amount)

    return {
        "buy_price": bybit_buy,
        "sells": {
            "BingX": bingx_sell,
            "HTX": htx_sell
        }
    }
