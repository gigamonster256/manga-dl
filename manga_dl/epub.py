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

    body_parts = []
    for i, img_path in enumerate(images):
        img_data = _webp_to_jpeg_bytes(img_path)
        img_item = epub.EpubItem(
            uid=f"img_{i:04d}",
            file_name=f"images/page_{i + 1:04d}.jpg",
            media_type="image/jpeg",
            content=img_data,
        )
        book.add_item(img_item)
        body_parts.append(
            f'<div style="text-align:center; page-break-after:always;">'
            f'<img src="images/page_{i + 1:04d}.jpg" alt="Page {i + 1}" '
            f'style="max-width:100%; height:auto; display:block; margin:0 auto;" />'
            f"</div>"
        )

    chapter = epub.EpubHtml(
        title=label,
        file_name="chapter.xhtml",
        lang="en",
    )
    chapter.content = "\n".join(body_parts)
    book.add_item(chapter)

    book.toc.append(chapter)
    book.spine = ["cover", chapter]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(output), book, {})
    return output
