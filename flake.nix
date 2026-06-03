{
  description = "Nixpkgs tracker notifier";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        packages.default = pkgs.python314Packages.buildPythonApplication {
          pname = "nixpkgs-notifier";
          version = "1.0";
          src = ./.;
          
          pyproject = true;
          build-system = [ pkgs.python314Packages.setuptools ];

          propagatedBuildInputs = with pkgs.python314Packages; [
            pycurl
            beautifulsoup4
            notify2
          ];
          buildInputs = [
            pkgs.matrix-commander-rs
          ];
        };
        mainProgram = "nixpkgs-notifier.py";
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/nixpkgs-notifier";
        };
      });
}
