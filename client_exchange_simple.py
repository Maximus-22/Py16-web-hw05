import aiohttp, argparse, asyncio, datetime, platform
# import sys


URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def main(shift_days: str) -> list:
    shift_days = int(shift_days)
    data_list_requests = []
    # for i in range(shift_days + 1):
    for i in range(shift_days):
        previous_date = datetime.datetime.now() - datetime.timedelta(days = i)
        formatted_date = previous_date.strftime("%d.%m.%Y")
        try:
            response = await request(URL + formatted_date)
            data_list_requests.append(response)
        except HttpError as err:
            print(err)
            return None
    return data_list_requests


# def parser_PB_json(pb_request: dict) -> dict:
#     parsed_PB_data = {}
#     parsed_PB_data[pb_request["date"]] = {}
    
#     for item in pb_request["exchangeRate"]:
#         if "saleRate" in item:
#             currency = item["currency"]
#             sale_rate = item["saleRate"]
#             purchase_rate = item["purchaseRate"]
#             parsed_PB_data[pb_request["date"]][currency] = {"sale": sale_rate, "purchase": purchase_rate}
    
#     return parsed_PB_data


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
    print(parsed_PB_data)
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
    # Виведення заголовку таблиці
    print("-"*44)
    print(header_format.format("Дата", "Валюта", "Продажа", "Покупка"))
    # Виведення даних у таблиці
    for date, currencies in data.items():
        print("-"*44)
        for currency, rates in currencies.items():
            print("{:<12} {:^10} {:<10} {:<10}".format(date, currency, rates['sale'], rates['purchase']))
    print("-"*44)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Створюємо парсер аргументів
    parser = argparse.ArgumentParser(description = "Отримати курси валют КБ \"Приватбанк\" не більше, ніж за останні 10 днів.")
    # Додаємо аргументи для вибору періоду та валют
    parser.add_argument("-d", "--days", help = "Часовий період запиту в днях.")
    parser.add_argument("-c", "--currencies", nargs="+", help = "Вибрані валюти - розділяються пробілами: CHF CZK EUR GBP PLN USD.")
    # Парсим аргументи командного рядка
    args = parser.parse_args()
    
    if args.days:
        selected_days = args.days
    else:
        selected_days = "2"
    if args.currencies:
        selected_currencies = args.currencies
    else:
        selected_currencies = ["EUR", "USD"]
    
    pb_requests = asyncio.run(main(selected_days))
    # print(pb_requests)
    result_by_default = get_currency_rates_all_days(parser_PB_json(pb_requests), selected_currencies)
    output_currency_rates_all_days(result_by_default)

    # if len(sys.argv) == 2 and 0 < int(sys.argv[1]) <= 10:
    #     pb_requests = asyncio.run(main(sys.argv[1]))
    #     # print(pb_requests)
    #     result_by_default = get_currency_rates_all_dates(parser_PB_json(pb_requests))
    #     output_currency_rates_all_dates(result_by_default)
    # else:
    #     print("Увага!\nПотрібно передати у программу як мінімум один строковий аргумент - ціле число.\n\
    #            Можна дізнатися курс валют не більше, ніж за останні 10 днів.")
    #     quit()