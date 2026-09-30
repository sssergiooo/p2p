import aiohttp
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_p2p_link(exchange: str, trade_type: str = "BUY", crypto: str = "USDT", currency: str = "KZT", amount: float = 10000.0) -> str:
    amount_str = str(int(amount))
    
    if exchange == "Binance":
        side = "SELL" if trade_type.upper() == "BUY" else "BUY"
        return f"https://p2p.binance.com/ru/trade/{side}/{crypto}?fiat={currency}&amount={amount_str}"
    
    elif exchange == "Bybit":
        action_type = "1" if trade_type.upper() == "BUY" else "0"
        return f"https://www.bybit.com/fiat/trade/otc/?actionType={action_type}&token={crypto}&fiat={currency}&amount={amount_str}"
    
    elif exchange == "BingX":
        return f"https://bingx.com/ru-ru/p2p/"
        
    return "https://t.me"

# 1. Покупка только с Bybit P2P
async def get_bybit_p2p_price(side: str = "1", token: str = "USDT", currency: str = "KZT", amount: float = 10000.0) -> float | None:
    """
    side: '1' для покупки (Buy), '0' для продажи (Sell).
    """
    url = "https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "tokenId": token,
        "currencyId": currency,
        "side": str(side),
        "size": "10",
        "page": "1",
        "amount": str(amount)
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
        logging.error(f"Ошибка Bybit P2P: {e}")
    return None

# 2. Продажа на Binance P2P
async def get_binance_p2p_price(trade_type: str = "SELL", asset: str = "USDT", fiat: str = "KZT", amount: float = 10000.0) -> float | None:
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": asset,
        "fiat": fiat,
        "merchantCheck": False,
        "page": 1,
        "rows": 10,
        "tradeType": trade_type,
        "transAmount": amount,
        "publisherType": None
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    advs = data.get("data", [])
                    if advs:
                        return float(advs[0]["adv"]["price"])
    except Exception as e:
        logging.error(f"Ошибка Binance P2P: {e}")
    return None

# 3. Продажа на BingX P2P
async def get_bingx_p2p_price(trade_type: str = "SELL", crypto: str = "USDT", fiat: str = "KZT", amount: float = 10000.0) -> float | None:
    """
    Парсер стакана BingX P2P
    """
    url = "https://open-api.bingx.com/openApi/p2p/v1/merchant/ad/list"
    # side: 1 - Buy, 2 - Sell
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
            async with session.get(url, params=params, headers=HEADERS, timeout=7) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ads = data.get("data", {}).get("ads", [])
                    if ads:
                        return float(ads[0]["price"])
    except Exception as e:
        logging.error(f"Ошибка BingX P2P: {e}")
    return None

async def scan_p2p_spreads(token: str = "USDT", currency: str = "KZT", amount: float = 10000.0) -> dict:
    """
    Собирает закуп с Bybit и продажи с Binance + BingX
    """
    bybit_buy = await get_bybit_p2p_price(side="1", token=token, currency=currency, amount=amount)
    
    binance_sell = await get_binance_p2p_price(trade_type="SELL", asset=token, fiat=currency, amount=amount)
    bingx_sell = await get_bingx_p2p_price(trade_type="SELL", crypto=token, fiat=currency, amount=amount)

    return {
        "buy_price": bybit_buy,
        "sells": {
            "Binance": binance_sell,
            "BingX": bingx_sell
        }
    }