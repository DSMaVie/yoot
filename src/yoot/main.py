from pathlib import Path
from typing import Annotated

import typer

from yoot.__version__ import version

app = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(version)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show the version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
):
    if version:
        raise typer.Exit()


@app.command()
def run(
    base_dir: Annotated[
        Path, typer.Argument(help="The main execution context.") + Path.cwd()
    ],
):
    base_dir = base_dir.resolve()
    typer.echo(f"Running at {base_dir} ...")


if __name__ == "__main__":
    app()
