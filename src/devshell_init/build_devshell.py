# This is the meat of the project: various heuristics to
# build a devshell for projects.

import json
import os
import re
import shlex
import subprocess
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


def get_current_system():  # pragma: no cover
    cp = subprocess.run(
        ["nix", "config", "show", "system"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return cp.stdout.strip()


def flake_has_devshell(
    flakeref: str, system: str, devshell: str
) -> bool:  # pragma: no cover
    # JSON strings are usually (always?) valid nix strings.
    escaped_devshell = json.dumps(devshell)

    cp = subprocess.run(
        [
            "nix",
            "eval",
            f"{flakeref}#devShells",
            "--apply",
            f"devShells: (devShells.{system}.{escaped_devshell} or false) != false",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return {
        "true": True,
        "false": False,
    }[cp.stdout.strip()]


def maybe_escape_flakeref_attr(attr: str) -> str:
    """
    >>> maybe_escape_flakeref_attr("vim")
    'vim'

    >>> maybe_escape_flakeref_attr("cubing.js")
    '"cubing.js"'

    >>> maybe_escape_flakeref_attr("cubing-js")
    'cubing-js'
    """

    ok_re = re.compile(r"[A-Za-z][-A-Za-z0-9]*")
    needs_escaping = not ok_re.fullmatch(attr)

    if needs_escaping:
        # JSON strings are usually (always?) valid nix strings.
        return json.dumps(attr)
    else:
        return attr


@devshell_builder
def maybe_devshed() -> MaybeDevshell:  # pragma: no cover
    if (devshed_flakeref := os.environ.get("DEVSHED_FLAKEREF")) is not None:
        prj_name = Path(".").resolve().name
        system = get_current_system()
        if flake_has_devshell(devshed_flakeref, system, prj_name):
            prj_name = shlex.quote(maybe_escape_flakeref_attr(prj_name))
            return {
                ENVRC: [f'use flake "$DEVSHED_FLAKEREF"#{prj_name}'],
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


@devshell_builder
def maybe_node() -> MaybeDevshell:  # pragma: no cover
    if Path("package-lock.json").exists():
        return {
            ENVRC: [
                "use nix -p nodejs",
            ],
        }

    return None
