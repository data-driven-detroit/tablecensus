from itertools import groupby
import pandas as pd

from .variables import collect_census_variables, create_namespace, unwrap_calculations
from .geography import build_api_geo_parts
from .request_prep import build_calls
from .request_manager import populate_data


def shorten_geoid(geoid: str):
    # 1400000US26163511400 -> 14000US26163511400

    return geoid[:5] + geoid[7:]


def assemble_from(dictionary_path, short_geoids=False, dump_raw=False):
    try:
        variables = pd.read_excel(dictionary_path, sheet_name="Variables")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"❌ Data dictionary file not found: {dictionary_path}\n"
            "Make sure the file path is correct and the file exists."
        )
    except ValueError as e:
        if "Variables" in str(e):
            raise ValueError(
                f"❌ Missing 'Variables' sheet in {dictionary_path}\n"
                "Your data dictionary must have a 'Variables' sheet. Use 'tablecensus start' to create a proper template."
            )
        raise ValueError(f"❌ Error reading Variables sheet: {e}")
    
    try:
        geographies = pd.read_excel(
            dictionary_path, sheet_name="Geographies", dtype="string"
        )
    except ValueError as e:
        if "Geographies" in str(e):
            raise ValueError(
                f"❌ Missing 'Geographies' sheet in {dictionary_path}\n"
                "Your data dictionary must have a 'Geographies' sheet with geography definitions."
            )
        raise ValueError(f"❌ Error reading Geographies sheet: {e}")
    
    try:
        releases = (
            pd.read_excel(dictionary_path, sheet_name="Years")
            .itertuples(index=False, name=None)
        )
    except ValueError as e:
        if "Years" in str(e):
            raise ValueError(
                f"❌ Missing 'Years' sheet in {dictionary_path}\n"
                "Your data dictionary must have a 'Years' sheet specifying which ACS years to include."
            )
        raise ValueError(f"❌ Error reading Years sheet: {e}")
    
    if variables.empty:
        raise ValueError("❌ Variables sheet is empty. Add at least one variable definition.")
    
    if geographies.empty:
        raise ValueError("❌ Geographies sheet is empty. Add at least one geography definition.")
    
    if not releases:
        raise ValueError("❌ Years sheet is empty. Add at least one year/release combination.")

    geo_parts = build_api_geo_parts(geographies)
    
    variable_stems, variable_codes = collect_census_variables(variables)
    
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

            active_cols = [c for c in columns if c in variable_codes]
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
            .assign(Year=year, Release=release)
        )
        result.append(frame)
    
    if not result:
        raise ValueError(
            "❌ No data was returned from the Census API.\n\n"
            "This usually means:\n"
            "  • Variable names in your Variables sheet don't exist in the Census API\n"
            "  • Geography codes in your Geographies sheet are invalid\n"
            "  • The combination of variables, geographies, and years doesn't exist\n"
            "  • All API requests failed (see errors above)\n\n"
            "Check your data dictionary and ensure:\n"
            "  • Variable names match Census variable codes (like B01001001)\n"
            "  • Geography codes are valid (use FIPS codes)\n"
            "  • Years match available ACS releases for your variables"
        )

    raw_census = pd.concat(result).reset_index(drop=True)
    
    if dump_raw:
        # Allow to dump the raw output for debugging
        raw_census.to_csv("dumped_output")

    namespace = create_namespace(raw_census, variable_stems)

    # Shorten the geoids if that's what the user would like
    if short_geoids:
        namespace["GEO_ID"]  = namespace["GEO_ID"].apply(shorten_geoid)

    result = [namespace["GEO_ID"], namespace["NAME"], namespace["Year"], namespace["Release"]]
    for _, variable in variables.iterrows():
        result.append(
            namespace.eval(variable["calculation"]).rename(variable["name"])
        )
    
    calculated = (
        pd.concat(result, axis=1)
        .rename(columns={"GEO_ID": "geoid", "NAME": "geoname"})
    )

    unwrapped = unwrap_calculations(calculated, variables) 

    return unwrapped
