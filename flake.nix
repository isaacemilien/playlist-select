{
  description = "Simple playlist selection tool written in Python";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.${system}.default = pkgs.python3Packages.buildPythonApplication {
        pname = "playlist-select";
        version = "0.1.0";
        src = ./.;
        format = "other";

        propagatedBuildInputs = with pkgs.python3Packages; [
          requests
        ];

        installPhase = ''
          mkdir -p $out/bin
          cp pls.py $out/bin/pls
          chmod +x $out/bin/pls
        '';
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs.python3Packages; [
          python
          requests
        ];
      };
    };
}
