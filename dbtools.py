from main import cur


def get_system(guild):  # Получение идентификатора экономической системы
    cur.execute(f"SELECT system FROM guilds WHERE guild = {guild}")
    system = cur.fetchone()
    if system:
        return system[0]
    raise SystemConnectionError


def get_currency(currency, system):  # Получение идентификатора валюты
    if not currency:
        cur.execute(f'SELECT default_currency FROM systems WHERE id = {system}')
        cur.execute(f'SELECT name FROM currencies WHERE system = {system} AND id = {cur.fetchone()[0]}')
        currency = cur.fetchone()
        if not currency:
            raise CurrencySetupError
        currency = currency[0]
    cur.execute(f"SELECT id FROM currencies WHERE name = '{currency}' and system = {system}")
    currency = cur.fetchone()
    if not currency:
        raise CurrencyNameError(currency)
    return currency[0]


def login(id, password):  # Проверка существования системы и правильности пароля
    cur.execute(f"SELECT password FROM systems WHERE id = {id}")
    system = cur.fetchone()
    if not system:
        raise SystemNotFindError
    return system[0] == password


class SystemConnectionError(Exception):
    ...


class CurrencyNameError(Exception):
    ...


class CurrencySetupError(Exception):
    ...


class SystemNotFindError(Exception):
    ...
