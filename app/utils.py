import functools
import requests
from flask import redirect, url_for, flash
from flask_login import current_user
from .models import Role


def require_roles(roles):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Insufficient permissions')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def load_countries():
    try:
        resp = requests.get('https://restcountries.com/v3.1/all?fields=name,currencies', timeout=30)
        resp.raise_for_status()
        data = resp.json()
        countries = []
        for c in data:
            name = c.get('name', {}).get('common')
            currencies = c.get('currencies', {})
            currency_codes = list(currencies.keys())
            countries.append({'name': name, 'currency': currency_codes[0] if currency_codes else 'USD'})
        countries.sort(key=lambda x: x['name'] or '')
        return countries
    except Exception:
        return [{'name': 'United States', 'currency': 'USD'}]


def get_currency_for_country(country_name: str) -> str | None:
    for c in load_countries():
        if c['name'] == country_name:
            return c['currency']
    return None
