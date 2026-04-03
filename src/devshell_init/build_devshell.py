# This is the meat of the project: various heuristics to
# build a devshell for projects.

from pathlib import Path


def build_devshell() -> dict[Path, list[str]] | None:
    """
    Return a devshell for the current directory.
    A devshell is a mapping of path to lines that should be in those files.
    """

    envrc = Path(".envrc")
    env_cmds: list[str] = []
    if Path("flake.nix").exists():
        env_cmds.append("use flake")
    else:
        return None

    return {
        envrc: env_cmds,
    }
