import ast

import pandas as pd
from .census_value import CensusValue


def extract_names(expr: str) -> set[str]:
    if pd.isna(expr) or not expr.strip():
        raise ValueError("Empty or missing calculation")
    
    try:
        tree = ast.parse(str(expr).strip(), mode="eval")
        return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    except SyntaxError as e:
        raise ValueError(f"Invalid calculation syntax: '{expr}'. Error: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing calculation '{expr}': {e}")


def collect_variables(indicators: pd.DataFrame) -> set:
    """
    'indicators' is the list of equations that comes out of the tablecensus
    spreadsheet. This reduces those to the minimal set required to request from
    the API.
    """
    all_vars = set()
    errors = []
    
    for i, (_, row) in enumerate(indicators.iterrows()):
        var_name = row.get("name", f"Variable {i+1}")
        calculation = row.get("calculation", "")
        
        try:
            extracted = extract_names(calculation)
            all_vars.update(extracted)
        except ValueError as e:
            errors.append(f"Row {i+2} ('{var_name}'): {e}")
    
    if errors:
        error_msg = "❌ Errors in Variables sheet:\n"
        for error in errors:
            error_msg += f"  • {error}\n"
        error_msg += "\nFix these issues and try again. Variables should be Census variable codes (like B01001001) or calculations (like B17001002 / B17001001)."
        raise ValueError(error_msg)
    
    if not all_vars:
        raise ValueError(
            "❌ No valid variables found in Variables sheet.\n"
            "Make sure your calculations contain valid Census variable codes."
        )
    
    return all_vars


def collect_census_variables(indicators: pd.DataFrame) -> tuple[list[str], list[str]]:
    """
    In this function we're calling the equations from the 'Variables' sheet 
    'indicators' to distinguish them from the census variables that we're trying
    to list out. So 'variables' are the raw numbers and 'indicators' are what
    we're trying to assemble.
    """
    result = []
    variable_stems = collect_variables(indicators)
    for v in variable_stems:
        result.append(f"{v[:-3]}_{v[-3:]}E") # Get estimate
        result.append(f"{v[:-3]}_{v[-3:]}M") # Get moe
    
    return list(variable_stems), result


def wrap_census_values(raw_census: pd.DataFrame, v):
    table = v[:-3]
    estimate_col = f"{table}_{v[-3:]}E"
    error_col = f"{table}_{v[-3:]}M"

    def wrapper(row):
        return CensusValue(row[estimate_col], row[error_col], table)

    return raw_census.apply(wrapper, axis=1)


def create_namespace(raw_census: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    header = {
        "GEO_ID": raw_census["GEO_ID"], 
        "NAME": raw_census["NAME"],
        "Year": raw_census["Year"],
        "Release": raw_census["Release"]
    }
    value_columns = {v: wrap_census_values(raw_census, v) for v in variables}

    return pd.DataFrame({**header, **value_columns})


def unwrap_calculations(results: pd.DataFrame, variables: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a frame that has named equations that are of the 'census_value' type
    and unravels them into their own 'estimate' 'moe' columns.

    What if it isn't a census value type?
    Check for API edge cases that may not have MOE -- though do this sooner than here.

    When creating the moe column name, let's try and help out the users who stick to
    snake case (with or without underscores / capitalization) by following their format
    with '_moe' appended. Any one else just gets 
    ' MOE' appended.

    # "snake_case" -> append '_moe'
    # "readable" -> append ' MOE'
    """
    unwrapped_data = {}
    
    # Copy over non-CensusValue columns as-is
    for col in results.columns:
        col_data = results[col]
        
        float_dtypes = []
        # Check if this column contains CensusValue objects
        if len(col_data) > 0 and isinstance(col_data.iloc[0], CensusValue):
            # Extract estimates and errors
            estimates = col_data.apply(lambda cv: cv.estimate)
            errors = col_data.apply(lambda cv: cv.error)
            
            # Determine MOE column naming convention based on variable name
            if '_' in col or col.islower():
                # snake_case pattern - append '_moe'
                moe_col = f"{col}_moe"
            else:
                # readable pattern - append ' MOE'
                moe_col = f"{col} MOE"
            
            unwrapped_data[col] = estimates
            unwrapped_data[moe_col] = errors

            float_dtypes.append(col)
            float_dtypes.append(moe_col)
        else:
            # Non-CensusValue column, copy as-is
            unwrapped_data[col] = col_data
    
    return pd.DataFrame(unwrapped_data, dtype={c: 'float' for c in float_dtypes})

