# This is the meat of the project: various heuristics to
# build a devshell for projects.

from pathlib import Path
from typing import Callable

MaybeDevshell = dict[Path, list[str]] | None

ENVRC = Path(".envrc")


DEVSHELL_BUILDERS: list[Callable[[], MaybeDevshell]] = []


def devshell_builder(builder: Callable[[], MaybeDevshell]):
    """
    Decorator to mark a function as a devshell builder.
    Kind of funky, but the order in which this is called affects
    the priority of the various devshell builders.
    """
    DEVSHELL_BUILDERS.append(builder)
    return builder


def build_devshell() -> MaybeDevshell:
    """
    Return a devshell for the current directory.
    A devshell is a mapping of path to lines that should be in those files.
    """
    for devshell_builder in DEVSHELL_BUILDERS:
        devshell = devshell_builder()
        if devshell is not None:
            return devshell

    return None


@devshell_builder
def maybe_flake() -> MaybeDevshell:  # pragma: no cover
    if Path("flake.nix").exists():
        return {
            ENVRC: ["use flake"],
        }

    return None


@devshell_builder
def maybe_go() -> MaybeDevshell:  # pragma: no cover
    if Path("go.mod").exists():
        return {
            ENVRC: ["use nix -p go"],
        }

    return None


@devshell_builder
def maybe_python() -> MaybeDevshell:  # pragma: no cover
    if (
        Path("pyproject.toml").exists()
        or Path("setup.py").exists()
        or Path("requirements.txt").exists()
    ):
        return {
            ENVRC: [
                "use nix -p python3",
                "layout python",
            ],
        }

    return None
