{
  buildPythonApplication,
  hatchling,
  typer,
}:

buildPythonApplication {
  name = "devshell-init";
  pyproject = true;
  build-system = [ hatchling ];
  src = ./.;

  dependencies = [
    typer
  ];
}
