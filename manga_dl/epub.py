import io
from pathlib import Path
from ebooklib import epub
from PIL import Image


def _stitch_group(paths: list[Path]) -> bytes:
    """Vertically stitch multiple images into one JPEG."""
    images = [Image.open(p).convert("RGB") for p in paths]
    total_h = sum(im.height for im in images)
    max_w = max(im.width for im in images)
    canvas = Image.new("RGB", (max_w, total_h))
    y = 0
    for im in images:
        canvas.paste(im, (0, y))
        y += im.height
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _group_images(paths: list[Path]) -> list[list[Path]]:
    """Group images into pages: tall images (>=500px) start a new page,
    short images (<500px) are stitched to the previous page."""
    groups: list[list[Path]] = []
    for p in paths:
        with Image.open(p) as im:
            h = im.height
        if h >= 500 or not groups:
            groups.append([p])
        else:
            groups[-1].append(p)
    return groups


def chapter_to_epub(
    image_dir: Path,
    metadata: dict,
    output: Path,
) -> Path:
    images = sorted(image_dir.rglob("*.webp"))
    if not images:
        raise RuntimeError(f"no webp files in {image_dir}")

    groups = _group_images(images)

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

    cover_data = _stitch_group(groups[0])
    book.set_cover("cover.jpg", cover_data)

    spine: list = ["cover"]
    for gi, group in enumerate(groups):
        page_num = gi + 1
        page_file = f"page_{page_num:04d}.xhtml"
        img_file = f"images/page_{page_num:04d}.jpg"
        img_label = label if page_num == 1 and len(groups) == 1 else f"Page {page_num}"

        img_data = _stitch_group(group)
        img_item = epub.EpubItem(
            uid=f"img_{gi:04d}",
            file_name=img_file,
            media_type="image/jpeg",
            content=img_data,
        )
        book.add_item(img_item)

        page = epub.EpubHtml(
            title=img_label,
            file_name=page_file,
            lang="en",
        )
        page.content = (
            '<div style="margin:0; padding:0; '
            'text-align:center;">'
            f'<img src="{img_file}" alt="{img_label}" '
            'style="max-width:100%; max-height:100vh; '
            'width:auto; height:auto; display:block; margin:0 auto;" />'
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
