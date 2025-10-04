import requests
from flask import current_app


def fetch_rates(base_currency: str) -> dict:
    url = f"{current_app.config['EXCHANGE_RATE_API_URL'].rstrip('/')}/{base_currency.upper()}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get('rates', {})


def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    if from_currency.upper() == to_currency.upper():
        return float(amount)
    rates = fetch_rates(from_currency)
    rate = rates.get(to_currency.upper())
    if rate is None:
        # Fallback: try reverse via base to USD then to target if available
        usd_rate = rates.get('USD')
        if usd_rate is None:
            raise ValueError(f"No conversion rate from {from_currency} to {to_currency}")
        # amount in USD
        amount_usd = float(amount) * usd_rate
        # fetch USD base
        usd_rates = fetch_rates('USD')
        target_rate = usd_rates.get(to_currency.upper())
        if target_rate is None:
            raise ValueError(f"No conversion rate to {to_currency}")
        return amount_usd * target_rate
    return float(amount) * float(rate)
