{
  lib,
  stdenv,
  python313,
  makeWrapper,
  gallery-dl,
  rev ? "dirty",
}:
let
  python = python313.withPackages (ps: [
    ps.ebooklib
    ps.pillow
  ]);
  pyprojectToml = lib.importTOML ./pyproject.toml;
in
stdenv.mkDerivation (finalAttrs: {
  pname = "manga-dl";
  version = "${pyprojectToml.project.version}-${rev}";

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.intersection (lib.fileset.fromSource (lib.sources.cleanSource ./.)) (
      lib.fileset.unions [
        ./manga_dl
      ]
    );
  };

  nativeBuildInputs = [ makeWrapper ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    site="$out/${python.sitePackages}"
    mkdir -p "$site"
    cp -r manga_dl "$site/"

    mkdir -p $out/bin
    makeWrapper ${python}/bin/python3 \
      $out/bin/${finalAttrs.meta.mainProgram} \
      --inherit-argv0 \
      --add-flags "-m manga_dl" \
      --prefix PATH : ${lib.makeBinPath [ gallery-dl ]} \
      --prefix PYTHONPATH : "$site"

    runHook postInstall
  '';

  meta = {
    description = "Manga downloader and EPUB converter";
    license = lib.licenses.mit;
    mainProgram = "manga-dl";
    inherit (python.meta) platforms;
  };
})
