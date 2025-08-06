from typing import Any
import asyncio

from aiohttp import ClientSession
from tqdm import tqdm


async def make_request(
    request: tuple[Any, str], session: ClientSession, pbar: tqdm
):
    label, url = request
    try:
        async with session.get(url, timeout=10) as r:
            r.raise_for_status()
            data = await r.json()
            pbar.update(1)

            return ("success", label, data)
    except Exception as e:
        pbar.update(1)
        return ("error", url, e)


async def manage_requests(requests: list[tuple[Any, str]]):
    with tqdm(total=len(requests), desc="Assembling table") as pbar:
        async with ClientSession() as session:
            results = await asyncio.gather(
                *(make_request(request, session, pbar) for request in requests)
            )

    ok = [(label, data) for status, label, data in results if status == "success"]
    errors = [(url, error) for status, url, error in results if status == "error"]

    return ok, errors


def populate_data(requests):
    ok, errors = asyncio.run(manage_requests(requests))

    for url, error in errors:
        print(f"Request failed for URL: {url} - {error}")
    
    return ok
