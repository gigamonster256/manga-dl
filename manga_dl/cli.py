import argparse
import re
import shutil
import sys
from pathlib import Path

from . import download, epub


def parse_chapter_range(spec: str) -> list[int]:
    chapters: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            chapters.update(range(int(a), int(b) + 1))
        else:
            chapters.add(int(part))
    return sorted(chapters)


def _is_series_url(url: str) -> bool:
    return bool(re.search(r"/manga/[^/]+$", url))


def _output_path(manga: str, chapter: int, minor: str, output_dir: Path) -> Path:
    slug = re.sub(r"[^\w\s-]", "", manga.lower()).replace(" ", "_")
    minor_suffix = minor.replace(".", "-") if minor else ""
    filename = f"{slug}_ch{chapter:04d}{minor_suffix}.epub"
    return output_dir / filename


def cmd_list(url: str) -> None:
    chapters = download.list_chapters(url)
    if not chapters:
        print("No chapters found.")
        return
    for ch_url, meta in chapters:
        ch = meta["chapter"]
        minor = meta.get("chapter_minor", "")
        label = f"Chapter {ch}{minor}" if minor else f"Chapter {ch}"
        print(f"  {label:20s}  {ch_url}")


def cmd_download(url: str, output_dir: Path) -> Path:
    meta, _pages = download.get_chapter_info(url)
    manga = meta.get("manga", "Unknown")
    ch = meta.get("chapter", 0)
    minor = meta.get("chapter_minor", "")
    label = f"Chapter {ch}{minor}" if minor else f"Chapter {ch}"
    count = meta.get("count", 0)

    print(f"Downloading: {manga} - {label} ({count} pages)")

    tmp = download.download_chapter(url)
    try:
        out = _output_path(manga, ch, minor, output_dir)
        out.parent.mkdir(parents=True, exist_ok=True)
        epub.chapter_to_epub(tmp, meta, out)
        print(f"Created: {out}")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_download_range(
    series_url: str,
    chapters: list[int],
    output_dir: Path,
) -> list[Path]:
    all_chapters = download.list_chapters(series_url)
    created: list[Path] = []

    url_map: dict[tuple[int, str], str] = {}
    for ch_url, meta in all_chapters:
        c = meta["chapter"]
        minor = meta.get("chapter_minor", "")
        url_map[(c, minor)] = ch_url

    wanted = set(chapters)
    for (c, minor), url in sorted(url_map.items()):
        if c in wanted and not minor:
            try:
                path = cmd_download(url, output_dir)
                created.append(path)
            except RuntimeError as e:
                print(f"Chapter {c} failed: {e}", file=sys.stderr)

    return created


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="manga-dl",
        description="Download manga chapters from Manganato and convert to EPUB",
    )
    parser.add_argument("url", help="Manganato series or chapter URL")
    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory (default: current dir)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List available chapters and exit",
    )
    parser.add_argument(
        "-c",
        "--chapters",
        help="Chapter range to download (e.g. '1-5', '1,3,5-10')",
    )
    parser.add_argument(
        "--browser",
        default="firefox",
        help="Browser to extract cookies from (default: firefox)",
    )

    args = parser.parse_args()
    output_dir = Path(args.output)
    download._BASE_ARGS[:] = ["--cookies-from-browser", args.browser]

    if args.list:
        cmd_list(args.url)
        return

    if args.chapters:
        if not _is_series_url(args.url):
            print(
                "Error: --chapters requires a series URL "
                "(e.g. https://www.manganato.gg/manga/manga-name)",
                file=sys.stderr,
            )
            sys.exit(1)
        ch_list = parse_chapter_range(args.chapters)
        created = cmd_download_range(args.url, ch_list, output_dir)
        print(f"\nDone. Created {len(created)} EPUB file(s).")
        return

    cmd_download(args.url, output_dir)
