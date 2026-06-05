{
  lib,
  python3Packages,
  makeWrapper,
  gallery-dl,
  rev ? "dirty",
}:
let
  pyprojectToml = lib.importTOML ./pyproject.toml;
in
python3Packages.buildPythonApplication (finalAttrs: {
  pname = "manga-dl";
  version = "${pyprojectToml.project.version}-${rev}";
  pyproject = true;

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.intersection (lib.fileset.fromSource (lib.sources.cleanSource ./.)) (
      lib.fileset.unions [
        ./manga_dl
        ./pyproject.toml
      ]
    );
  };

  build-system = [ python3Packages.setuptools ];

  dependencies = [
    python3Packages.ebooklib
    python3Packages.pillow
  ];

  makeWrapperArgs = [
    "--prefix"
    "PATH"
    ":"
    "${lib.makeBinPath [ gallery-dl ]}"
  ];

  checkPhase = ''
    runHook preCheck
    $out/bin/manga-dl --help
    runHook postCheck
  '';

  meta = {
    description = "Manga downloader and EPUB converter";
    license = lib.licenses.mit;
    mainProgram = "manga-dl";
  };
})
