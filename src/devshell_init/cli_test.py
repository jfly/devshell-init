import subprocess
from pathlib import Path

from typer.testing import CliRunner

from .cli import app


def check_run(args: list[str]) -> str:
    cp = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE)
    return cp.stdout


class TestDiff:
    def test_not_a_git_repo(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("flake.nix").touch()

            result = runner.invoke(app, ["--check"])
            assert (result.exit_code, result.output) == (
                1,
                "This doesn't look like a git repo\n",
            )

    def test_check(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()

            result = runner.invoke(app, ["--check", "--verbose"])
            assert (result.exit_code, result.output) == (
                0,
                "File is missing: .envrc\nuse flake\n\nAll good!\n",
            )

    def test_ignores_comments(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()
            Path(".envrc").write_text("# this is a cool comment\nuse flake")

            result = runner.invoke(app, ["--check"])
            assert (result.exit_code, result.output) == (
                0,
                "All good!\n",
            )

    def test_diff(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()
            Path(".envrc").write_text("# this is a cool comment\nuse flakey")

            result = runner.invoke(app, ["--check", "--verbose"])
            assert (result.exit_code, result.output) == (
                1,
                "File doesn't match: .envrc\n"
                "--- actual-.envrc\n"
                "+++ expected-.envrc\n"
                "@@ -1 +1 @@\n"
                "-use flakey\n"
                "+use flake\n"
                "\n",
            )

    def test_tracked_devshell(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()
            envrc = Path(".envrc")
            envrc.write_text("# this is a cool comment\nuse flakey")
            check_run(["git", "add", "--intent-to-add", str(envrc)])

            result = runner.invoke(app, ["--check"])
            assert (result.exit_code, result.output) == (
                0,
                "I see these path(s) are tracked:\n"
                "  .envrc\n"
                "There must be a dev shell already provided by this repo.\n",
            )


class TestCreate:
    def test_create(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()

            result = runner.invoke(app, ["--exclude", "--verbose"])
            assert (result.exit_code, result.output) == (
                0,
                "Updating: .git/info/exclude\nCreating: .envrc\nAll good!\n",
            )
            assert Path(".envrc").read_text() == "use flake\n"
            assert Path(".git/info/exclude").read_text() == "/.envrc\n/.direnv/\n"

    def test_force(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            check_run(["git", "init"])
            Path("flake.nix").touch()
            envrc = Path(".envrc")
            envrc.write_text("bogus")

            result = runner.invoke(app, ["--force"])
            assert (result.exit_code, result.output) == (
                0,
                "Updating: .envrc\nAll good!\n",
            )
            envrc = Path(".envrc")
            assert envrc.read_text() == "use flake\n"
