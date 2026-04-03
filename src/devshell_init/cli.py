import subprocess
from difflib import unified_diff
from pathlib import Path
from typing import Annotated

import typer

from .build_devshell import build_devshell

app = typer.Typer()


def get_diff_ignoring_comments(p: Path, expected_lines: list[str]) -> str | None:
    actual_lines = [
        line for line in p.read_text().splitlines() if not line.startswith("#")
    ]

    if actual_lines != expected_lines:
        return "".join(
            unified_diff(
                [f"{line}\n" for line in actual_lines],
                [f"{line}\n" for line in expected_lines],
                fromfile=f"actual-{p}",
                tofile=f"expected-{p}",
            )
        )

    return None


def is_all_comments(contents: str) -> bool:
    r"""
    Checks if all lines of the given contents are either empty, or are a comment.

    >>> is_all_comments("# comment1")
    True

    >>> is_all_comments("# comment1\n\n# comment2")
    True

    >>> is_all_comments("# comment1\n\nline1")
    False
    """
    return all(line == "" or line.startswith("#") for line in contents.splitlines())


def is_tracked(p: Path) -> bool:
    cp = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(p)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return cp.returncode == 0


def to_abs_repo_path(rel_path: Path) -> str:
    """
    Convert a path relative to a repo root to an "absolute" path (relative to the repo root).
    Useful for `.gitignore` files and the like.

    >>> to_abs_repo_path(Path(".envrc"))
    '/.envrc'
    """
    assert not rel_path.is_absolute()
    return "/" + str(rel_path)


def join_lines(lines: list[str]) -> str:
    r"""
    Join lines, including a trailing newline.

    >>> join_lines(["line1", "line2"])
    'line1\nline2\n'

    >>> join_lines([])
    '\n'
    """
    return "\n".join(lines) + "\n"


@app.command()
def main(
    check: Annotated[
        bool,
        typer.Option(
            help="Do not create a devshell, instead check if the current project has one we can recreate. It's OK if the project doesn't have a devshell.",
        ),
    ] = False,
    exclude: Annotated[
        bool,
        typer.Option(
            help="Add files to .git/info/exclude",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            help="Verbose output",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            help="Force updating files, even if they exist with different contents.",
        ),
    ] = False,
):
    if not Path(".git").exists():
        print("This doesn't look like a git repo")
        raise typer.Exit(1)

    maybe_create = build_devshell()
    if maybe_create is None:
        print("I'm not sure how to create a devshell for this project")
        raise typer.Exit(1)

    tracked_files = [p for p in maybe_create.keys() if is_tracked(p)]
    if len(tracked_files) > 0:
        pretty_paths = "\n".join(f"  {p}" for p in tracked_files)
        print(f"I see these path(s) are tracked:\n{pretty_paths}")
        print("There must be a dev shell already provided by this repo.")
        return

    if exclude:
        maybe_create[Path(".git/info/exclude")] = [
            *(to_abs_repo_path(p) for p in maybe_create.keys()),
            "/.direnv/",
        ]

    to_create: dict[Path, list[str]] = {}
    to_update: dict[Path, tuple[list[str], str]] = {}
    for path, lines in maybe_create.items():
        if not path.exists():
            to_create[path] = lines
        elif (diff := get_diff_ignoring_comments(path, lines)) is not None:
            to_update[path] = (lines, diff)

    errors = False

    if len(to_update) > 0:
        for path, (lines, diff) in to_update.items():
            current_contents = path.read_text()
            all_comments = is_all_comments(current_contents)

            if not force and not all_comments:
                errors = True
                print(f"File doesn't match: {path}")
                if verbose:
                    print(diff)
            else:
                print(f"Updating: {path}")
                path.write_text(join_lines(lines))

    if len(to_create) > 0:
        # Note: we don't mark this as `errors = True`, because missing files are easily recreated.
        # It's differing files that are a problem (see `to_update` above).

        for path, lines in to_create.items():
            if check:
                print(f"File is missing: {path}")
                if verbose:
                    print(join_lines(lines))
            else:
                print(f"Creating: {path}")
                path.write_text(join_lines(lines))

    if errors:
        raise typer.Exit(1)
    else:
        print("All good!")


if __name__ == "__main__":
    app()  # pragma: no cover
