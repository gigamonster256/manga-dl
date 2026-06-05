{
  description = "Manga downloader and EPUB converter";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      systems = [
        "x86_64-linux"
      ];
      forEachSystem = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
      rev = self.shortRev or self.dirtyShortRev or "dirty";
    in
    {
      packages = forEachSystem (pkgs: rec {
        default = manga-dl;
        manga-dl = pkgs.callPackage ./package.nix { inherit rev; };
      });
      formatter = forEachSystem (pkgs: pkgs.nixfmt-tree);
      devShells = forEachSystem (pkgs: {
        default = import ./shell.nix { inherit pkgs; };
      });
      overlays = {
        default = final: prev: {
          manga-dl = final.callPackage ./package.nix { inherit rev; };
        };
      };
    };
}
