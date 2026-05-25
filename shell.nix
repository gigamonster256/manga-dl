{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  buildInputs = [
    pkgs.gallery-dl
    pkgs.black
    (pkgs.python3.withPackages (ps: [
      ps.ebooklib
      ps.pillow
    ]))
  ];

  # add self to PYTHONPATH so that we can import manga_dl in the dev shell
  shellHook = ''
    export PYTHONPATH="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD"):$PYTHONPATH"
  '';
}
