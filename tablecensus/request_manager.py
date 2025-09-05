from typing import Any
import asyncio

from aiohttp import ClientSession, ClientResponseError, ClientTimeout
from tqdm import tqdm


async def make_request(
    request: tuple[Any, str], session: ClientSession, pbar: tqdm
):
    label, url = request
    try:
        async with session.get(url, timeout=ClientTimeout(total=30)) as r:
            r.raise_for_status()
            data = await r.json()
            pbar.update(1)
            return (label, data)
    except ClientResponseError as e:
        if e.status == 400:
            return RequestError(f"Invalid request for {label}: Check your variable names and geography codes. Census API returned: {e.message}")
        elif e.status == 404:
            return RequestError(f"Data not found for {label}: The combination of variables, geography, and year may not be available in the Census API")
        elif e.status == 500:
            return RequestError(f"Census API server error for {label}: Try again later or check if the data exists for this time period")
        else:
            return RequestError(f"API request failed for {label} (HTTP {e.status}): {e.message}")
    except asyncio.TimeoutError:
        return RequestError(f"Request timeout for {label}: Census API took too long to respond. Try again later.")
    except Exception as e:
        return RequestError(f"Unexpected error for {label}: {str(e)}")


class RequestError(Exception):
    pass


async def manage_requests(requests: list[tuple[Any, str]]):
    with tqdm(total=len(requests), desc="Assembling table") as pbar:
        async with ClientSession() as session:
            results = await asyncio.gather(
                *(make_request(request, session, pbar) for request in requests)
            )

    ok = [r for r in results if not isinstance(r, (Exception, RequestError))]
    errors = [e for e in results if isinstance(e, (Exception, RequestError))]

    return ok, errors


def populate_data(requests):
    ok, errors = asyncio.run(manage_requests(requests))

    if errors:
        print("\n❌ Errors occurred while fetching data from Census API:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        
        if len(errors) == len(requests):
            raise RuntimeError(
                "\n💥 All API requests failed. Common causes:\n"
                "  • Invalid variable names in Variables sheet\n"
                "  • Invalid geography codes in Geographies sheet\n" 
                "  • Requesting data that doesn't exist for the specified year/geography combination\n"
                "  • Census API is temporarily unavailable\n\n"
                "Double-check your data dictionary and try again."
            )
        elif len(errors) > len(requests) * 0.5:
            print(f"\n⚠️  Warning: {len(errors)}/{len(requests)} requests failed. Results may be incomplete.")
    
    return ok
