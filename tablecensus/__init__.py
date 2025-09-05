from pathlib import Path
import shutil
from importlib.resources import files, as_file
import datetime
import click

from .assemble import assemble_from
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

    print(f"Created a new data dictionary at {path}")


@main.command()
@click.argument(
    "dictionary_path",
)
@click.argument(
    "output_path", 
    default=f"report_{TODAY}.xlsx",
)
@click.option(
    "-s",
    "--short-geoids",
    is_flag=True,
)
def assemble(dictionary_path, output_path, short_geoids):
    print(f"Assembling data from dictionary {dictionary_path} and saving to {output_path}")
    
    final = assemble_from(dictionary_path, short_geoids)
    path = Path(output_path)

    if path.suffix == ".xlsx":
        apply_d3_style(final).to_excel(output_path, index=False)

    elif path.suffix == ".csv":
        final.to_csv(output_path, index=False)

    elif path.suffix == ".parquet":
        final.to_parquet(path, index=False)

