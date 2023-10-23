import asyncio, datetime, logging

import aiofile, httpx, names, websockets
from aiopath import AsyncPath
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


async def request(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        rqst = await client.get(url)
        if rqst.status_code == 200:
            result = rqst.json()
            return result
        else:
            raise Exception(f"HTTPError status: {rqst.status_code} for {url}.")
        # else:
        #     return "Щось пійшло не за планом ..."


async def get_exchange() -> list:
    try:
        response = await request(f'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
        # # потім у функції [distrubute] ми відправляємо результат [response] до тунелю [ws: WebSocketServerProt], але
        # # за допомогою під'єднаного socket можна передати або str(), або byte_str();
        # # то ж [response] обгортаємо у str() -> [str(response)]
        # return str(response)
        # наразі вивід буде перероблений у більш придатний вигляд, та переданий у функцію-форматтер, тому саме в цьому
        # випадку повертаємо dict()
        return response
    except Exception as err:
        print(f"The request caught HTTPError {err}.")
        return None


async def output_currency(data: list) -> str:    
    exchange_frame = "Курс гривні Приватбанку: "
    for item in data:
        exchange_frame += f'{item["ccy"]} - купівля {item["buy"]}, продаж {item["sale"]}; '
    return exchange_frame[:-2]


async def write_exchange_log(message: str):
    log_file = AsyncPath("log.txt")
    async with aiofile.async_open(log_file, mode = "a") as f:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%d.%m.%Y %H:%M:%S")
        await f.write(f"[{formatted_time}] -> {message}\n")


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        # надаємо випадкове ім'я з пакету [names]
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        # [message] приходить від [main.js] при натисканні у [index.html] кнопки [Send message] -> "submit"
        async for message in ws:
            if message == "exchange":
                # exchange = await get_exchange()
                raw_exchange = await get_exchange()
                exchange = await output_currency(raw_exchange)
                await self.send_to_clients(exchange)
                await write_exchange_log("There is command \"exchange\" executed.")
            elif message == "Hello server" or message == "Hello all":
                await self.send_to_clients("Wellcome to the dangerous road!")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
