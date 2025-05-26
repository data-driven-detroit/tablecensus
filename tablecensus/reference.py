"""
There is a lot of futzing with the census geographies to request
exactly the data you want. This file provides a bunch of translations
to get from one representation to another for summary levels.
"""

from enum import Enum, auto


class SumLevel(Enum):
    """
    SumLevel is the default way to ID which geo type is in play
    around the library. Other representations are allowed only
    at the end-user interface: the 'create_geography' function call,
    and the final call out to the census api where you have to use
    their (surprisingly complicated) strings.
    """

    NATION = auto()
    STATE = auto()
    CONGRESSIONAL_DISTRICT = auto()
    STATE_LEG_LOWER = auto()
    STATE_LEG_UPPER = auto()
    COUNTY = auto()
    ZCTA = auto()
    COUNTY_SUBDIVISION = auto()
    PLACE = auto()
    TRACT = auto()
    BLOCK_GROUP = auto()
    ELEM_SCH_DISTRICT = auto()
    SEC_SCH_DISTRICT = auto()
    UNI_SCH_DISTRICT = auto()


class UCG(Enum):
    """
    This is a one member enum to mark that the geoid part is all that is
    needed to define the item.
    """

    ID = auto()


# translate the 'part' to the enum

STRING_NAME_TRANSLATION = {
    "nation": SumLevel.NATION,
    "state": SumLevel.STATE,
    "congressional_district": SumLevel.CONGRESSIONAL_DISTRICT,
    "state_leg_lower": SumLevel.STATE_LEG_LOWER,
    "state_leg_upper": SumLevel.STATE_LEG_UPPER,
    "county": SumLevel.COUNTY,
    "zcta": SumLevel.ZCTA,
    "county_subdivision": SumLevel.COUNTY_SUBDIVISION,
    "place": SumLevel.PLACE,
    "tract": SumLevel.TRACT,
    "block_group": SumLevel.BLOCK_GROUP,
    "elem_sch_district": SumLevel.ELEM_SCH_DISTRICT,
    "sec_sch_district": SumLevel.SEC_SCH_DISTRICT,
    "uni_sch_district": SumLevel.UNI_SCH_DISTRICT,
}

NAME_STRING_TRANSLATION = {
    val: key for key, val in STRING_NAME_TRANSLATION.items()
}

# use the IPUMS sumlev representation to get to the enum

SUMLEV_LABELS = {
    "01000": SumLevel.NATION,
    "04000": SumLevel.STATE,
    "50000": SumLevel.CONGRESSIONAL_DISTRICT,
    "05000": SumLevel.COUNTY,
    "86000": SumLevel.ZCTA,
    "62000": SumLevel.STATE_LEG_LOWER,
    "61000": SumLevel.STATE_LEG_UPPER,
    "06000": SumLevel.COUNTY_SUBDIVISION,
    "16000": SumLevel.PLACE,
    "14000": SumLevel.TRACT,
    "15000": SumLevel.BLOCK_GROUP,
    "95000": SumLevel.ELEM_SCH_DISTRICT,
    "96000": SumLevel.SEC_SCH_DISTRICT,
    "97000": SumLevel.UNI_SCH_DISTRICT,
}

SUMLEV_TO_STEM = {val: key for key, val in SUMLEV_LABELS.items()}

# For building the final call to the census API

API_GEO_PARAMS = {
    SumLevel.NATION: "us",
    SumLevel.STATE: "state",
    SumLevel.CONGRESSIONAL_DISTRICT: "congressional district",
    SumLevel.COUNTY: "county",
    SumLevel.ZCTA: "zip code tabulation area",
    SumLevel.STATE_LEG_LOWER: "state legislative district (upper chamber)",
    SumLevel.STATE_LEG_UPPER: "state legislative district (lower chamber)",
    SumLevel.COUNTY_SUBDIVISION: "county subdivision",
    SumLevel.PLACE: "place",
    SumLevel.TRACT: "tract",
    SumLevel.BLOCK_GROUP: "block group",
    SumLevel.ELEM_SCH_DISTRICT: "school district (elementary)",  # These can't be created through this builder.
    SumLevel.SEC_SCH_DISTRICT: "school district (secondary)",
    SumLevel.UNI_SCH_DISTRICT: "school district (unified)",
}

GEO_TO_API_PARAMS = {val: key for key, val in API_GEO_PARAMS.items()}

API_STR_TO_VAR_STR = {
    key: NAME_STRING_TRANSLATION[val] for key, val in GEO_TO_API_PARAMS.items()
}

# This shows which part consumes how many digits on a geoid

GEOID_DECOMPOSER = {
    SumLevel.NATION: {SumLevel.NATION: 0},
    SumLevel.STATE: {SumLevel.STATE: 2},
    SumLevel.COUNTY: {SumLevel.STATE: 2, SumLevel.COUNTY: 3},
    SumLevel.CONGRESSIONAL_DISTRICT: {
        SumLevel.STATE: 2,
        SumLevel.CONGRESSIONAL_DISTRICT: 2,
    },
    SumLevel.ZCTA: {SumLevel.STATE: 0, SumLevel.ZCTA: 5},
    SumLevel.STATE_LEG_LOWER: {SumLevel.STATE: 2, SumLevel.STATE_LEG_LOWER: 3},
    SumLevel.STATE_LEG_UPPER: {SumLevel.STATE: 2, SumLevel.STATE_LEG_UPPER: 3},
    SumLevel.COUNTY_SUBDIVISION: {
        SumLevel.STATE: 2,
        SumLevel.COUNTY: 3,
        SumLevel.COUNTY_SUBDIVISION: 5,
    },
    SumLevel.PLACE: {SumLevel.STATE: 2, SumLevel.PLACE: 5},
    SumLevel.TRACT: {SumLevel.STATE: 2, SumLevel.COUNTY: 3, SumLevel.TRACT: 6},
    SumLevel.BLOCK_GROUP: {
        SumLevel.STATE: 2,
        SumLevel.COUNTY: 3,
        SumLevel.TRACT: 6,
        SumLevel.BLOCK_GROUP: 1,
    },
    SumLevel.ELEM_SCH_DISTRICT: {
        SumLevel.STATE: 2,
        SumLevel.ELEM_SCH_DISTRICT: 5,
    },
    SumLevel.SEC_SCH_DISTRICT: {
        SumLevel.STATE: 2,
        SumLevel.SEC_SCH_DISTRICT: 5,
    },
    SumLevel.UNI_SCH_DISTRICT: {
        SumLevel.STATE: 2,
        SumLevel.UNI_SCH_DISTRICT: 5,
    },
}

# If you only know which parts are present, this gets you back to
# which geoid is being built.

SUMLEV_FROM_PARTS = {
    frozenset(parts.keys()): lev for lev, parts in GEOID_DECOMPOSER.items()
} | {
    frozenset([SumLevel.ZCTA]): SumLevel.ZCTA
}  # Handling the post-2020 case

# Nation has to be handeled separately
SUMLEV_FROM_PARTS[frozenset({SumLevel.NATION})] = SumLevel.NATION


class ACSEra(Enum):
    ONE_YEAR = auto()
    THREE_YEAR = auto()
    FIVE_YEAR = auto()


# Maps era identifiers to ACSEra values
ERA_MAPPINGS = {
    "acs1": ACSEra.ONE_YEAR,
    "acs3": ACSEra.THREE_YEAR,
    "acs5": ACSEra.FIVE_YEAR,
}

ERA_STR_TRANSLATION = {val: key for key, val in ERA_MAPPINGS.items()}


# Valid years for each ACSEra type
VALID_YEARS_BY_ERA = {
    ACSEra.ONE_YEAR: range(2005, 2024),  # Example range for 1-year data
    ACSEra.THREE_YEAR: range(
        2005, 2014
    ),  # 3-year data was discontinued in 2014
    ACSEra.FIVE_YEAR: range(2009, 2024),  # Example range for 5-year data
}


