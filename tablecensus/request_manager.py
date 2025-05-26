from typing import Any
import asyncio

from aiohttp import ClientSession


async def make_request(request: tuple[Any, str], session: ClientSession):
    label, url = request
    async with session.get(url, timeout=10) as r:
        r.raise_for_status()
        data = await r.json()

        return (label, data)


async def manage_requests(requests: list[tuple[Any, str]]):
    async with ClientSession() as session:
        results = await asyncio.gather(
            *(make_request(request, session) for request in requests),
            return_exceptions=True
        )

    ok = [r for r in results if not isinstance(r, Exception)]
    errors = [e for e in results if isinstance(e, Exception)]

    return ok, errors


def populate_data(requests):
    ok, errors = asyncio.run(manage_requests(requests))

    for error in errors:
        print(error)
    
    return ok
