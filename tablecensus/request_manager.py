"""Fetch Census API responses concurrently, with bounded parallelism and retries.

Three problems this module previously had, all of which surfaced as confusing
errors far from their cause:

1. UNBOUNDED CONCURRENCY. `asyncio.gather` fired every request at once. A large
   data dictionary (hundreds of variables x several geographies x several years)
   produced hundreds of simultaneous requests, which the Census API answers
   slowly or not at all -- so the client caused the very timeouts it reported.

2. NO RETRY. A single transient timeout permanently discarded that chunk of
   variables. Census wildcard requests (all ZCTAs in a state, say) are routinely
   slow rather than broken, so this lost data that a second attempt would get.

3. PARTIAL RESULTS RETURNED AS SUCCESS. When some requests failed the caller
   still received the successful ones and carried on, so the failure resurfaced
   later as `KeyError: 'B25003G_002E'` -- a variable that was fine, in a chunk
   that never arrived. Silent partial data is worse than a hard failure in an
   ETL, so incomplete fetches now raise.

Tunable through the environment:

    CENSUS_MAX_CONCURRENCY   simultaneous requests            (default 8)
    CENSUS_REQUEST_TIMEOUT   seconds per attempt              (default 120)
    CENSUS_MAX_RETRIES       attempts after the first         (default 3)
    CENSUS_ALLOW_PARTIAL     "1" to return partial results    (default off)
"""

import asyncio
import os
import random
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout
from tqdm import tqdm


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


MAX_CONCURRENCY = _env_int("CENSUS_MAX_CONCURRENCY", 8)
REQUEST_TIMEOUT = _env_int("CENSUS_REQUEST_TIMEOUT", 120)
MAX_RETRIES = _env_int("CENSUS_MAX_RETRIES", 3)
ALLOW_PARTIAL = os.environ.get("CENSUS_ALLOW_PARTIAL", "").strip() in {"1", "true", "yes"}

# 400/404 mean the request itself is wrong -- a bad variable name or geography.
# Retrying cannot help and only slows the failure down.
PERMANENT_STATUSES = {400, 404}


class RequestError(Exception):
    pass


async def make_request(
    request: tuple[Any, str],
    session: ClientSession,
    pbar: tqdm,
    semaphore: asyncio.Semaphore,
):
    label, url = request
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with semaphore:
                async with session.get(
                    url, timeout=ClientTimeout(total=REQUEST_TIMEOUT)
                ) as r:
                    r.raise_for_status()
                    data = await r.json()
                    pbar.update(1)
                    return (label, data)

        except ClientResponseError as e:
            if e.status in PERMANENT_STATUSES:
                pbar.update(1)
                if e.status == 400:
                    return RequestError(
                        f"Invalid request for {label}: Check your variable names "
                        f"and geography codes. Census API returned: {e.message}")
                return RequestError(
                    f"Data not found for {label}: The combination of variables, "
                    f"geography, and year may not be available in the Census API")
            last_error = f"HTTP {e.status}: {e.message}"

        except asyncio.TimeoutError:
            last_error = f"timed out after {REQUEST_TIMEOUT}s"

        except ClientError as e:
            last_error = f"connection error: {e}"

        except Exception as e:  # noqa: BLE001 - reported, not swallowed
            pbar.update(1)
            return RequestError(f"Unexpected error for {label}: {e}")

        if attempt < MAX_RETRIES:
            # Exponential backoff with jitter, so retries do not resynchronise
            # into another burst against an API that is already struggling.
            delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)

    pbar.update(1)
    return RequestError(
        f"Request failed for {label} after {MAX_RETRIES + 1} attempts "
        f"({last_error}). Lower CENSUS_MAX_CONCURRENCY (currently "
        f"{MAX_CONCURRENCY}) or raise CENSUS_REQUEST_TIMEOUT (currently "
        f"{REQUEST_TIMEOUT}s)."
    )


async def manage_requests(requests: list[tuple[Any, str]]):
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    with tqdm(total=len(requests), desc="Assembling table") as pbar:
        async with ClientSession() as session:
            results = await asyncio.gather(
                *(make_request(r, session, pbar, semaphore) for r in requests)
            )

    ok = [r for r in results if not isinstance(r, (Exception, RequestError))]
    errors = [e for e in results if isinstance(e, (Exception, RequestError))]
    return ok, errors


def populate_data(requests):
    ok, errors = asyncio.run(manage_requests(requests))

    if not errors:
        return ok

    print("\n❌ Errors occurred while fetching data from Census API:")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")

    if len(errors) == len(requests):
        raise RuntimeError(
            "\n💥 All API requests failed. Common causes:\n"
            "  • Invalid variable names in Variables sheet\n"
            "  • Invalid geography codes in Geographies sheet\n"
            "  • Requesting data that doesn't exist for the specified "
            "year/geography combination\n"
            "  • Census API is temporarily unavailable\n\n"
            "Double-check your data dictionary and try again."
        )

    if ALLOW_PARTIAL:
        print(f"\n⚠️  {len(errors)}/{len(requests)} requests failed. "
              "CENSUS_ALLOW_PARTIAL is set, so returning incomplete results -- "
              "expect missing variables downstream.")
        return ok

    # Returning partial data makes the failure resurface much later as a
    # KeyError on some unrelated variable that happened to share the chunk.
    raise RuntimeError(
        f"\n💥 {len(errors)} of {len(requests)} API requests failed, so the "
        "result would be missing variables.\n"
        "  Returning partial data here surfaces later as a KeyError naming a "
        "variable that was never the problem.\n\n"
        "  • Transient? Retries are already applied "
        f"({MAX_RETRIES} after the first attempt).\n"
        "  • Still timing out? Lower CENSUS_MAX_CONCURRENCY or raise "
        "CENSUS_REQUEST_TIMEOUT.\n"
        "  • Need the partial result anyway? Set CENSUS_ALLOW_PARTIAL=1."
    )
