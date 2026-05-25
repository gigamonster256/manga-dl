import io
from pathlib import Path
from ebooklib import epub
from PIL import Image


def _webp_to_jpeg_bytes(path: Path) -> bytes:
    with Image.open(path) as img:
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def chapter_to_epub(
    image_dir: Path,
    metadata: dict,
    output: Path,
) -> Path:
    images = sorted(image_dir.rglob("*.webp"))
    if not images:
        raise RuntimeError(f"no webp files in {image_dir}")

    chapter_num = metadata.get("chapter", 0)
    chapter_minor = metadata.get("chapter_minor", "")
    manga_title = metadata.get("manga", "Unknown")
    author = metadata.get("author", "Unknown")

    label = f"Chapter {chapter_num}{chapter_minor}"
    epub_title = f"{manga_title} - {label}"

    series_index = float(
        f"{chapter_num}{chapter_minor}" if chapter_minor else str(chapter_num)
    )

    book = epub.EpubBook()
    book.set_identifier(f"manga-dl-{hash(epub_title) & 0xFFFFFFFFFFFFFFFF:x}")
    book.set_title(epub_title)
    book.set_language("en")
    book.add_author(author)

    book.add_metadata(
        None, "meta", "", {"name": "calibre:series", "content": manga_title}
    )
    book.add_metadata(
        None, "meta", "", {"name": "calibre:series_index", "content": str(series_index)}
    )

    cover_data = _webp_to_jpeg_bytes(images[0])
    book.set_cover("cover.jpg", cover_data)

    num_pages = len(images)
    spine: list = ["cover"]
    for i, img_path in enumerate(images):
        uid = f"page_{i:04d}"
        img_file = f"images/page_{i + 1:04d}.jpg"

        if i == 0:
            img_data = cover_data
        else:
            img_data = _webp_to_jpeg_bytes(img_path)

        img_item = epub.EpubItem(
            uid=f"img_{i:04d}",
            file_name=img_file,
            media_type="image/jpeg",
            content=img_data,
        )
        book.add_item(img_item)

        page = epub.EpubHtml(
            title=f"Page {i + 1}" if i > 0 or num_pages > 1 else label,
            file_name=f"page_{i + 1:04d}.xhtml",
            lang="en",
        )
        page.content = (
            '<div style="text-align:center; '
            'display:flex; align-items:center; justify-content:center; '
            'height:100vh; margin:0; padding:0;">'
            f'<img src="{img_file}" alt="Page {i + 1}" '
            'style="max-width:100%; max-height:100%; object-fit:contain;" />'
            "</div>"
        )
        book.add_item(page)
        spine.append(page)

    book.spine = spine
    book.toc = [spine[1]] if len(spine) > 1 else []

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(output), book, {})
    return output
