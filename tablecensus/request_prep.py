from itertools import product

from .config import get_api_key


MAX_VARS_PER_CALL = 25


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def build_calls(geo_parts, variables, releases):
    # chunk out var string to 50 vars

    template = (
        "https://api.census.gov/data/{year}/acs/{release}"
        "?get=GEO_ID,NAME,{vars_str}&{geo_part}{key_string}"
    )

    api_key = get_api_key()
    if not api_key:
        from .config import _config_path
        raise RuntimeError(
            "No Census API key found.\n\n"
            f"  Expected config file: {_config_path()}\n\n"
            "  Create that file with:\n\n"
            "    [census]\n"
            '    api_key = "YOUR_KEY"\n\n'
            "  Get a free key at https://api.census.gov/data/key_signup.html"
        )
    key_string = f"&key={api_key}"

    return [
        (
            (geo_part, year, release),
            template.format(
                vars_str=",".join(vars_str),
                geo_part=geo_part,
                key_string=key_string,
                year=year,
                release=release,
            )
        )
        for geo_part, vars_str, (year, release) in product(
            geo_parts, chunk(list(variables), MAX_VARS_PER_CALL), releases
        )
    ]
