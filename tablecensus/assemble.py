from itertools import groupby
import pandas as pd

from .variables import create_renamer
from .geography import build_api_geo_parts
from .request_prep import build_calls
from .request_manager import populate_data


def assemble_from(dictionary_path):
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
    responses = populate_data(calls)
    
    grouped_responses = []
    # Group by label for east-west grouping
    for label, (_, group) in groupby(responses, key=lambda r: r[0]):
        grouped_responses.append(
            (
                label,
                pd.concat(
                    (frame.set_index("GEO_ID") for frame in group)
                )
            )
        )

    result = []
    for response in grouped_responses:
        (_, year, release), data = response # skip the geo stuff
        columns, *row = data
        
        frame = (
            pd.DataFrame(row, columns=columns)
            .rename(columns=rename)
            .astype({var: pd.Int64Dtype() for var in rename.values()})
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
        .rename(columns={"GEO_ID": "geoid", "NAME": "Geography Name"})
    )
