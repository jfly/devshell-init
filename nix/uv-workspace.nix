{ inputs, ... }:
{
  imports = [
    ./uv2nix.nix
    inputs.devshell.flakeModule
  ];

  perSystem =
    { pkgs, ... }:
    {
      uv2nix = {
        python = pkgs.python313;

        workspaceRoot = ./..;
        nativeCheckInputs = [
          # Used in <src/devshell_init/cli_test.py>
          pkgs.git
        ];
      };
    };
}
