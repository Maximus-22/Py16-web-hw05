import aiohttp, argparse, asyncio, datetime, platform
# import sys


URL = "https://api.privatbank.ua/p24api/exchange_rates?date="


class HttpError(Exception):
    pass


async def request(session, url: str):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result
            else:
                raise HttpError(f"Error status: {resp.status} for {url}")
    except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
        raise HttpError(f'Connection error: {url}', str(err))


async def main(shift_days: str):
    shift_days = int(shift_days)
    tasks = []
    async with aiohttp.ClientSession() as session:
        # for i in range(shift_days + 1):
        for i in range(shift_days):
            previous_date = datetime.datetime.now() - datetime.timedelta(days = i)
            formatted_date = previous_date.strftime("%d.%m.%Y")
            url = URL + formatted_date
            try:
                tasks.append(request(session, url))
            except HttpError as err:
                print(err)
                return None
        responses = await asyncio.gather(*tasks)
        return responses


def parser_PB_json(pb_request: list) -> dict:
    parsed_PB_data = {}
    for data in pb_request:
        date = data["date"]
        parsed_PB_data[date] = {}
    
        for item in data["exchangeRate"]:
            if "saleRate" in item:
                currency = item["currency"]
                sale_rate = item["saleRate"]
                purchase_rate = item["purchaseRate"]
                parsed_PB_data[date][currency] = {"sale": sale_rate, "purchase": purchase_rate}

    return parsed_PB_data


def get_currency_rates_all_days(data: dict, currencies: list) -> dict:
    result = {}
    for date, rates in data.items():
        result[date] = {}
        for currency in currencies:
            if currency in rates and isinstance(rates[currency], dict):
                result[date][currency] = rates[currency]
            # else:
            #     result[date][currency] = "Currency not found"
    return result


def output_currency_rates_all_days(data: dict) -> None:
    header_format = "{:^12} {:^10} {:<10} {:<10}"
    # Вывод заголовка таблицы
    print("-"*44)
    print(header_format.format("Дата", "Валюта", "Продажа", "Покупка"))
    # Вывод данных в таблице
    for date, currencies in data.items():
        print("-"*44)
        for currency, rates in currencies.items():
            print("{:<12} {:^10} {:<10} {:<10}".format(date, currency, rates['sale'], rates['purchase']))
    print("-"*44)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser(description = "Отримати курси валют КБ \"Приватбанк\" не більше, ніж за останні 10 днів.")
    parser.add_argument("-d", "--days", help = "Часовий період запиту в днях.")
    parser.add_argument("-c", "--currencies", nargs="+", help = "Вибрані валюти - розділяються пробілами: : CHF CZK EUR GBP PLN USD.")
    args = parser.parse_args()
    
    if args.days:
        selected_days = args.days
    else:
        selected_days = "1"
    if args.currencies:
        selected_currencies = args.currencies
    else:
        selected_currencies = ["EUR", "USD"]

    loop = asyncio.get_event_loop()
    pb_requests = loop.run_until_complete(main(selected_days))
    result_by_default = get_currency_rates_all_days(parser_PB_json(pb_requests), selected_currencies)
    output_currency_rates_all_days(result_by_default)
    
    # if len(sys.argv) == 2 and 0 <= int(sys.argv[1]) <= 10:
    #     loop = asyncio.get_event_loop()
    #     pb_request = loop.run_until_complete(main(sys.argv[1]))
    #     print(pb_request)
    # else:
    #     print("Увага!\nПотрібно передати у программу як мінімум один строковий аргумент - ціле число.\n\
    #            Можна дізнатися курс валют не більше, ніж за останні 10 днів.")
    #     quit()