from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import quote

import pandas as pd

from .reference import (
    SumLevel,
    STRING_NAME_TRANSLATION,
    SUMLEV_FROM_PARTS,
    API_GEO_PARAMS,
)


@dataclass(eq=True)
class Geography:
    sum_level: SumLevel
    parts: dict
    ucgid: bool = False

    @property
    def parents(self) -> frozenset[tuple[SumLevel, str]] | SumLevel:
        """
        Parents returns tuples of parent sum_levels and their integer
        values (as strings).
        """
        key = frozenset(
            {
                (key, val)
                for key, val in self.parts.items()
                if key != self.sum_level
            }
        )

        if not key:
            return self.sum_level

        return key

    @property
    def identity(self):
        return self.parts[self.sum_level]


def create_geography_from_parts(parts):
    if "nation" in parts:
        return Geography(
            sum_level=SumLevel.NATION,
            parts={SumLevel.NATION: "1"},
        )
    try:
        parts = {
            STRING_NAME_TRANSLATION[part_name]: str(part_val)
            for part_name, part_val in parts.items()
        }

        return Geography(
            sum_level=SUMLEV_FROM_PARTS[frozenset(parts.keys())],
            parts=parts,
        )

    except KeyError:
        available_parts = list(STRING_NAME_TRANSLATION.keys())
        raise ValueError(
            f"❌ Invalid geography combination: {', '.join(parts.keys())}\n\n"
            f"Valid geography parts are: {', '.join(available_parts)}\n\n"
            "Common geography combinations:\n"
            "  • state: 26 (Michigan)\n"
            "  • state + county: 26, 163 (Wayne County, Michigan)\n"
            "  • state + county + tract: 26, 163, 123456\n"
            "  • state + place: 26, 22000 (Detroit city)\n\n"
            "See: https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html"
        )


def consolidate_calls(geos: list[Geography]) -> defaultdict:
    """
    This takes a list of geographies and organizes them by their parent
    geographies.
    """

    tree = defaultdict(list)

    for geo in geos:
        tree[(geo.sum_level, geo.parents)].append(geo)

    return tree


def create_consolodated_api_calls(tree: defaultdict):
    """
    This takes the CallTree created by 'consolidate_calls' and returns
    a list of the geography portion of the api calls.
    """

    calls = []
    # You don't need the sumlevel, you just need separate line items in
    # the defaultdict in the CallTree
    for (_, parents), children in tree.items():
        child_str = ",".join([child.identity for child in children])

        match parents:
            case SumLevel():
                calls.append(
                    f"for={quote(API_GEO_PARAMS[parents])}:{child_str}"
                )

            case frozenset():
                child_str = ",".join({child.identity for child in children})
                ingeos = "%20".join(
                    f"{quote(API_GEO_PARAMS[key])}:{val}"
                    for key, val in parents
                )

                sumlevel = children[0].sum_level

                for_str = f"for={quote(API_GEO_PARAMS[sumlevel])}:{child_str}"
                in_str = f"in={ingeos}"

                calls.append(f"{for_str}&{in_str}")

            case _:
                raise TypeError(f"{type(parents)} isn't a valid parent type.")

    return calls


def match_geo(row):
    return {k: v for k, v in row.items() if pd.notna(v)}


def build_api_geo_parts(geographies):
    try:
        matched_geos = geographies.apply(match_geo, axis=1)
        if matched_geos.empty or all(not geo for geo in matched_geos):
            raise ValueError(
                "❌ No valid geographies found in Geographies sheet.\n"
                "Make sure you have at least one row with valid geography codes."
            )
        
        geography_objects = []
        for i, geo_parts in enumerate(matched_geos):
            if not geo_parts:  # Skip empty rows
                continue
            try:
                geo_obj = create_geography_from_parts(geo_parts)
                geography_objects.append(geo_obj)
            except ValueError as e:
                print(f"⚠️  Warning: Row {i+2} in Geographies sheet has invalid data: {e}")
                continue
        
        if not geography_objects:
            raise ValueError(
                "❌ No valid geographies could be created from your Geographies sheet.\n"
                "Check that your geography codes are valid and properly formatted."
            )
        
        return create_consolodated_api_calls(consolidate_calls(geography_objects))
    except Exception as e:
        if "❌" in str(e):  # Re-raise our custom errors
            raise
        raise ValueError(f"❌ Error processing geographies: {e}")
