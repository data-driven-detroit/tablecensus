import ast
from functools import reduce

import pandas as pd


def extract_names(expr: str) -> set[str]:
    try:
        tree = ast.parse(expr, mode="eval")
        return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    except TypeError:
        print("At least one variable is improperly defined. Review 'Variables' tab in datadictionary file. Skipping for now.")
        return set()


def collect_variables(variables: pd.DataFrame) -> set:
    return reduce(
        set.union, 
        variables["calculation"].apply(extract_names).values
    )


def transform_variable(variable: str) -> str:
    return f"{variable[:-3]}_{variable[-3:]}E"


def create_renamer(variables: pd.DataFrame):
    return {
        transform_variable(var): var for var in collect_variables(variables)
    }
