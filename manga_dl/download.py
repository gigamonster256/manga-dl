import json
import shutil
import subprocess
import tempfile
from pathlib import Path


_BASE_ARGS: list[str] = ["--cookies-from-browser", "firefox"]


def _gallery_dl(*args: str) -> subprocess.CompletedProcess:
    cmd = ["gallery-dl", *_BASE_ARGS, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def _parse_json_output(text: str) -> list:
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return []


def list_chapters(url: str) -> list[tuple[str, dict]]:
    result = _gallery_dl("--dump-json", url)
    chapters: list[tuple[str, dict]] = []
    for msg in _parse_json_output(result.stdout):
        if isinstance(msg, list) and len(msg) > 2 and msg[0] == 6:
            chapters.append((msg[1], msg[2]))
    return chapters


def get_chapter_info(url: str) -> tuple[dict, list[dict]]:
    result = _gallery_dl("--dump-json", url)
    metadata: dict = {}
    pages: list[dict] = []
    for msg in _parse_json_output(result.stdout):
        if not isinstance(msg, list) or len(msg) < 2:
            continue
        if msg[0] == 2:
            metadata = msg[1]
        elif msg[0] == 3:
            pages.append(msg[2])
    return metadata, pages


def download_chapter(url: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="manga-dl-"))
    _gallery_dl("-D", str(tmp), url)
    images = sorted(tmp.rglob("*.webp"))
    if not images:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError("no images downloaded")
    return tmp
