import pandas as pd
from tablecensus.variables import create_namespace, unwrap_calculations
from tablecensus.census_value import CensusValue


def test_create_namespace():
    variables = ["B01001001", "B01001002"]
    raw_census_data = pd.DataFrame({
        "GEO_ID": ["1", "2", "3", "4", "5"],
        "NAME": ["one", "two", "three", "four", "five"],
        "Year": [2020, 2020, 2020, 2020, 2020],
        "Release": ["acs5", "acs5", "acs5", "acs5", "acs5"],
        "B01001_001E": [11, 10, 18, 23, 14],
        "B01001_001M": [2, 2, 4, 2, 3],
        "B01001_002E": [5, 5, 5, 5, 5],
        "B01001_002M": [1, 1, 1, 1, 1],
    })
    
    namespace = create_namespace(raw_census_data, variables)

    assert "GEO_ID" in namespace.columns
    assert "B01001001" in namespace.columns
    
    assert namespace.shape == (5, 6)

    assert isinstance(namespace.iloc[0, 4], CensusValue)
    assert isinstance(namespace.iloc[0, 5], CensusValue)


def test_unwrap_calculations():
    variables = ["B01001001", "B01001002"]
    raw_census_data = pd.DataFrame({
        "GEO_ID": ["1", "2", "3", "4", "5"],
        "NAME": ["one", "two", "three", "four", "five"],
        "Year": [2020, 2020, 2020, 2020, 2020],
        "Release": ["acs5", "acs5", "acs5", "acs5", "acs5"],
        "B01001_001E": [11, 10, 18, 23, 14],
        "B01001_001M": [2, 2, 4, 2, 3],
        "B01001_002E": [5, 5, 5, 5, 5],
        "B01001_002M": [1, 1, 1, 1, 1],
    })

    namespace = create_namespace(raw_census_data, variables)
    variables_df = pd.DataFrame()  # Empty DataFrame as second parameter
    unwrapped = unwrap_calculations(namespace, variables_df)

