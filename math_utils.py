def calculate_net_spread(
    buy_price: float, 
    sell_price: float, 
    amount_fiat: float, 
    network_fee_crypto: float = 1.0,
    buy_fee_pct: float = 0.0,
    sell_fee_pct: float = 0.0,
    **kwargs
) -> dict:
    """Универсальный расчет спреда и чистой прибыли со всеми ключами"""
    if not buy_price or not sell_price or buy_price <= 0:
        return {
            "gross_spread": 0.0,
            "net_spread": 0.0,
            "net_profit": 0.0,
            "profit": 0.0,
            "spread": 0.0,
            "total_fee_pct": 0.0,
            "total_fee": 0.0,
            "network_fee": 0.0
        }

    # 1. Грязный спред
    gross_spread = ((sell_price - buy_price) / buy_price) * 100

    # 2. Покупка крипты с учетом комиссии биржи
    crypto_bought = (amount_fiat / buy_price) * (1 - buy_fee_pct / 100)

    # 3. Вычитаем комиссию сети (1 USDT)
    crypto_after_network = crypto_bought - network_fee_crypto

    if crypto_after_network <= 0:
        return {
            "gross_spread": round(gross_spread, 2),
            "net_spread": 0.0,
            "net_profit": 0.0,
            "profit": 0.0,
            "spread": 0.0,
            "total_fee_pct": round(buy_fee_pct + sell_fee_pct, 2),
            "total_fee": 0.0,
            "network_fee": network_fee_crypto
        }

    # 4. Продажа за фиат
    final_fiat = (crypto_after_network * sell_price) * (1 - sell_fee_pct / 100)

    # 5. Итоговый профит и чистый спред
    net_profit = final_fiat - amount_fiat
    net_spread = (net_profit / amount_fiat) * 100

    total_fee_pct = round(buy_fee_pct + sell_fee_pct + ((network_fee_crypto * sell_price / amount_fiat) * 100), 2)
    total_fee = round(amount_fiat - (final_fiat - net_profit), 2)

    return {
        "gross_spread": round(gross_spread, 2),
        "net_spread": round(net_spread, 2),
        "spread": round(net_spread, 2),
        "net_profit": round(net_profit, 2),
        "profit": round(net_profit, 2),
        "total_fee_pct": total_fee_pct,
        "total_fee": total_fee,
        "network_fee": network_fee_crypto
    }