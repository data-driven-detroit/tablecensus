from pathlib import Path
import shutil
from importlib.resources import files, as_file
import datetime
import click
import pandas as pd

from .variables import create_renamer
from .geography import build_api_geo_parts
from .request_prep import build_calls
from .request_manager import populate_data
from .table_style import apply_d3_style


TODAY = datetime.date.today().strftime("%Y%m%d")


@click.group()
def main():
    pass


@main.command()
@click.argument(
    "destination", 
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=".",
)
def start(destination):
    path = destination / f"data_dictionary_{TODAY}.xlsx"

    tmpl_dir = files("tablecensus") / "templates"
    tmpl = tmpl_dir / f"dictionary_template.xlsx"
    with as_file(tmpl) as src_path:
        shutil.copyfile(src_path, path)

    print(f"Created a new data dictionary at f{path}")


@main.command()
@click.argument(
    "dictionary_path",
)
@click.argument(
    "output_path", 
    default=f"report_{TODAY}.xlsx",
)
def assemble(dictionary_path, output_path):
    # TODO -- this is great for a cli, but I NEED to be callable from code as well
    print(f"Assembling data from dictionary {dictionary_path} and saving to {output_path}")

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
    
    result = []
    for response in responses:
        (year, release), data = response
        columns, *row = data
        
        frame = (
            pd.DataFrame(row, columns=columns)
            .rename(columns=rename)
            .astype({var: pd.Int64Dtype() for var in rename.values()})
            .assign(Year=year, Release=release)
        )
        result.append(frame)

    namespace = pd.concat(result).reset_index(drop=True)

    result = [namespace["GEO_ID"], namespace["NAME"], namespace["Year"], namespace["Release"]]
    for _, variable in variables.iterrows():
        result.append(
            namespace.eval(variable["calculation"]).rename(variable["name"])
        )

    final = (
        pd.concat(result, axis=1)
        .rename(columns={"GEO_ID": "geoid", "NAME": "Geography Name"})
    )

    apply_d3_style(final).to_excel(output_path, index=False)

