from itertools import groupby
import pandas as pd

from .variables import create_renamer
from .geography import build_api_geo_parts
from .request_prep import build_calls
from .request_manager import populate_data


def shorten_geoid(geoid: str):
    # 1400000US26163511400 -> 14000US26163511400

    return geoid[:5] + geoid[7:]


def assemble_from(dictionary_path, short_geoids=False):
    variables = pd.read_excel(dictionary_path, sheet_name="Variables")
    geographies = pd.read_excel(
        dictionary_path, sheet_name="Geographies", dtype="string"
    )
    releases = (
        pd.read_excel(dictionary_path, sheet_name="Years")
        .itertuples(index=False, name=None)
    )
    geo_parts = build_api_geo_parts(geographies)

    rename = create_renamer(variables)
    variable_codes = list(rename.keys())
    
    calls = build_calls(geo_parts, variable_codes, releases)

    # The calls are broken up by year and head of geography tree
    responses = populate_data(calls)
    

    grp_key = lambda r: r[0]

    grouped_responses = []
    # Group by label for east-west concatenation
    for label, group in groupby(sorted(responses, key=grp_key), key=grp_key):
        
        variable_batches = []
        for _, data in group:
            columns, *rows = data

            active_cols = [c for c in columns if c in rename]
            header = active_cols.copy()
            header.append("GEO_ID")

            if not variable_batches:
                # Include the name of the first group
                header.append("NAME")

            frame = (
                pd.DataFrame(rows, columns=columns)[header]
                .astype({var: pd.Float64Dtype() for var in active_cols})
                .set_index(["GEO_ID"])
            )

            variable_batches.append(frame)

        grouped_responses.append(
            (label, pd.concat(variable_batches, axis=1).reset_index())
        )


    result = []
    # North-south concatenation for different geos / years
    for response in grouped_responses:
        (_, year, release), data = response # skip the geo stuff
        frame = (
            data
            .rename(columns=rename)
            .assign(Year=year, Release=release)
        )
        result.append(frame)
    
    if not result:
        raise ValueError("Nothing was returned from API, check variable and geography definitions.")

    namespace = pd.concat(result).reset_index(drop=True)

    result = [namespace["GEO_ID"], namespace["NAME"], namespace["Year"], namespace["Release"]]
    for _, variable in variables.iterrows():
        result.append(
            namespace.eval(variable["calculation"]).rename(variable["name"])
        )

    return (
        pd.concat(result, axis=1)
        .rename(columns={"GEO_ID": "geoid", "NAME": "geoname"})
    )
