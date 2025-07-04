from typing import Any
import asyncio

from aiohttp import ClientSession
from tqdm import tqdm


async def make_request(
    request: tuple[Any, str], session: ClientSession, pbar: tqdm
):
    label, url = request
    async with session.get(url, timeout=10) as r:
        r.raise_for_status()
        data = await r.json()
        pbar.update(1)

        return (label, data)


async def manage_requests(requests: list[tuple[Any, str]]):
    with tqdm(total=len(requests), desc="Assembling table") as pbar:
        async with ClientSession() as session:
            results = await asyncio.gather(
                *(make_request(request, session, pbar) for request in requests),
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
