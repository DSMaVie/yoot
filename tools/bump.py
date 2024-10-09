import re
from enum import StrEnum, auto
from pathlib import Path
from turtle import up
from typing import Annotated, Self

import typer
from pydantic import BaseModel, Field
from rich import print


class Files(BaseModel):
    version_file: Annotated[Path, Field(init=False)] = Path("src/yoot/__version__.py")
    pyproject_file: Annotated[Path, Field(init=False)] = Path("pyproject.toml")


STANDALONE_SEMVER_REGEX = re.compile(r"^(\d+)\.(\d+)\.(\d+)(-rc\.(\d+))?$")
PREFIXED_SEMVER_REGEX = re.compile(
    r"^version\s*=\s*\"(\d+)\.(\d+)\.(\d+)(-rc\.(\d+))?\"$"
)


class BumpType(StrEnum):
    MAJOR = auto()
    MINOR = auto()
    PATCH = auto()
    RC = auto()


class Version(BaseModel):
    major: int
    minor: int
    patch: int
    rc: int | None = None

    @classmethod
    def from_string(cls, version_str: str) -> Self | None:
        if not (match := cls.scan(version_str)):
            return None

        major, minor, patch, _, rc = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            rc=int(rc) if rc else None,
        )

    @staticmethod
    def scan(version_str: str) -> re.Match[str] | None:
        return STANDALONE_SEMVER_REGEX.match(
            version_str
        ) or PREFIXED_SEMVER_REGEX.match(version_str)

    def bump(self, which: BumpType = BumpType.RC) -> Self:
        match which:
            case BumpType.MAJOR:
                return self.model_copy(
                    update={"major": self.major + 1, "minor": 0, "patch": 0, "rc": None}
                )
            case BumpType.MINOR:
                return self.model_copy(
                    update={"minor": self.minor + 1, "patch": 0, "rc": None}
                )
            case BumpType.PATCH:
                return self.model_copy(update={"patch": self.patch + 1, "rc": None})
            case BumpType.RC:
                return self.model_copy(update={"rc": (self.rc or 0) + 1})


def get_version_from_file(file_path: Path) -> Version | None:
    with file_path.open("r") as file:
        lines = file.readlines()
        lines = (line.strip() for line in lines)

    return next(
        (Version.from_string(line) for line in lines if Version.scan(line)), None
    )


def update_version_in_file(file_path: Path, new_version: Version) -> None:
    new_version_str = f'version = "{new_version}"'

    with file_path.open("r") as file:
        lines = file.readlines()
        lines = (line.strip() for line in lines)
        lines = [new_version_str if Version.scan(line) else line for line in lines]

    with file_path.open("w") as file:
        file.writelines(lines)


def main(
    project_dir: Annotated[
        Path, typer.Argument(help="The main execution context.")
    ] = Path.cwd(),
    bump_type: Annotated[
        BumpType, typer.Option(help="The type of bump to do.")
    ] = BumpType.RC,
):
    files: dict[str, Path] = Files().model_dump()
    current_version: None | Version = None
    new_version: None | Version = None

    for file in files.values():
        file_path: Path = project_dir / file

        if not file_path.exists():
            raise typer.BadParameter(
                f"[bold red]File {file_path} does not exist.[/bold red]"
            )

        if this_files_version := get_version_from_file(file_path):
            current_version = current_version or this_files_version
            new_version = new_version or current_version.bump(bump_type)

        if current_version != this_files_version:
            raise typer.BadParameter(
                f"[bold red]File {file} has a different version from the others.[/bold red]"
            )

        if new_version is None:
            raise typer.BadParameter(
                f"[bold red]Could not find a version in {file}.[/bold red]"
            )

        update_version_in_file(file_path, new_version)
        print(
            f"[bold green]Bumped {file} version {new_version}[/bold green]"
        )  # TODO: make info logging


if __name__ == "__main__":
    typer.run(main)
    # TODO: test this script
