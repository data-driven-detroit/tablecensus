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
        raise ValueError(
            f"The components you provided, {', '.join(parts.keys())}, are not "
            "valid geography parts or don't constitute a complete census "
            "geography specification. See "
            "https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html"
            " for more information, or check the d3census docs."
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
    return create_consolodated_api_calls(
        consolidate_calls(
            geographies
            .apply(match_geo, axis=1)
            .apply(create_geography_from_parts)
            .values
        )
    )
