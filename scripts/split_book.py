#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pypdf>=5.0",
#   "ebooklib>=0.18",
#   "beautifulsoup4>=4.12",
#   "lxml>=5.0",
# ]
# ///

"""
Split a PDF or EPUB book into per-chapter files.

Usage:
    split_book.py <book_path> <output_dir>

Output:
    <output_dir>/chapters.json      metadata (book title, chapter list, file paths)
    <output_dir>/chapters/ch01_<slug>.{pdf,txt}
    <output_dir>/chapters/ch02_<slug>.{pdf,txt}
    ...

PDF: chapters split by PDF outline/bookmarks. Errors out if no outline exists.
EPUB: chapters taken from the nav/TOC, each saved as UTF-8 text.

Exit codes:
    0  success
    1  unexpected error
    2  unsupported format (not .pdf or .epub)
    3  no TOC/outline — cannot auto-split
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pypdf
from bs4 import BeautifulSoup
from ebooklib import epub


SAFE_CHARS_PATTERN = re.compile(r'[\\/:"*?<>|\n\r\t]+')
WHITESPACE_COLLAPSE = re.compile(r"\s+")

# Body-length threshold below which a chapter is recommended to skip
# (typically pure title pages like "Part I" with no real content).
MIN_BODY_LENGTH = 500

# Title patterns matched case-insensitively against the chapter title.
# Chapters with matching titles are flagged skip_recommended=True regardless
# of body length — these are frontmatter / backmatter that are never the
# "formal content" of a book. Preface / Foreword / Introduction / Prologue /
# Epilogue are NOT in this list because they typically contain author-written
# content; if they happen to be empty they're caught by MIN_BODY_LENGTH.
SKIP_TITLE_PATTERNS = [
    # English frontmatter
    r"^cover$",
    r"^(half[\s-]?)?title\s+page$",
    r"^copyright(\b|$)",
    r"^(table\s+of\s+)?contents$",
    r"^dedication$",
    r"^epigraph$",
    r"^list\s+of\s+(figures|illustrations|tables|maps|plates)",
    r"^frontispiece$",
    # English backmatter
    r"^acknowled?ge?ments?$",  # acknowledgments / acknowledgements (US/UK, sg/pl)
    r"^(end)?notes?$",
    r"^footnotes?$",
    r"^bibliography$",
    r"^(works|further)\s+(cited|reading)$",
    r"^references$",
    r"^index$",
    r"^(art|illustration|picture|photo|image)\s+credits$",
    r"^credits$",
    r"^about\s+the\s+authors?$",
    r"^author'?s?\s+bio(graphy)?$",
    r"^glossary$",
    r"^appendix(\b|$|:)",
    r"^appendices$",
    r"^colophon$",
    r"^also\s+by\s+",  # "Also by Author Name"
    # Chinese frontmatter
    r"^(封面|扉页|版权页?|版权(声明|信息)?)$",
    r"^(目|目录|目錄)$",
    r"^(献辞|题词|题献)$",
    # Chinese backmatter
    r"^致谢$",
    r"^(尾)?注释?$",
    r"^(参考)?文献$",
    r"^参考文献$",
    r"^索引$",
    r"^(关于作者|作者简介)$",
    r"^(词汇|术语)表$",
    r"^附录(\b|$|：|:)",
]
SKIP_TITLE_REGEX = re.compile("|".join(SKIP_TITLE_PATTERNS), re.IGNORECASE)


def is_title_skip_recommended(title: str) -> bool:
    """True if the chapter title matches a known frontmatter/backmatter pattern."""
    return bool(SKIP_TITLE_REGEX.match(title.strip()))


def compute_skip_recommended(title: str, body_length: int) -> tuple[bool, str]:
    """Return (skip_recommended, reason) for a chapter."""
    if is_title_skip_recommended(title):
        return True, "frontmatter/backmatter"
    if body_length < MIN_BODY_LENGTH:
        return True, f"body_length={body_length} < {MIN_BODY_LENGTH}"
    return False, ""


def slugify(title: str, max_len: int = 40) -> str:
    """Strip filesystem-unsafe chars, collapse whitespace, trim. Preserve CJK."""
    s = SAFE_CHARS_PATTERN.sub("", title).strip()
    s = WHITESPACE_COLLAPSE.sub("-", s)
    s = s.strip("-.")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-.")
    return s or "untitled"


def sanitize_book_title(raw: str) -> str:
    """Book title: same rules as slug but keep spaces (replace only truly unsafe)."""
    s = SAFE_CHARS_PATTERN.sub("", raw).strip()
    s = WHITESPACE_COLLAPSE.sub(" ", s)
    return s or "untitled"


# ---------------------------------------------------------------------- PDF


def _pdf_walk_outline(outline, reader: pypdf.PdfReader, depth: int = 0):
    """Yield (title, page_index, depth) from a (possibly nested) pypdf outline."""
    for item in outline:
        if isinstance(item, list):
            yield from _pdf_walk_outline(item, reader, depth + 1)
        else:
            try:
                page = reader.get_destination_page_number(item)
            except Exception:
                continue
            title = str(getattr(item, "title", "")).strip()
            if not title:
                continue
            yield (title, page, depth)


def _pick_chapter_depth(entries):
    """Pick the shallowest depth where we have ≥3 entries.

    Rationale: many PDFs have depth=0 as Parts (too coarse) and depth=1 as
    Chapters (right level). Picking shallowest with ≥3 items handles both
    "flat chapter list" and "nested parts→chapters" cases.
    """
    counts = Counter(d for _, _, d in entries)
    if not counts:
        return None
    for d in sorted(counts):
        if counts[d] >= 3:
            return d
    return min(counts)


def extract_pdf_chapters(book_path: Path, output_dir: Path) -> dict:
    reader = pypdf.PdfReader(str(book_path))

    outline = reader.outline
    if not outline:
        raise NoTOCError(
            f"PDF 无书签/TOC，无法自动拆分章节。\n"
            f"建议：用 Calibre 的 'Polish books → Update metadata / Add TOC' 给 {book_path.name} 加目录后重试。"
        )

    all_entries = list(_pdf_walk_outline(outline, reader))
    if not all_entries:
        raise NoTOCError(f"PDF 的 outline 解析出的有效条目为 0 — {book_path.name}")

    chapter_depth = _pick_chapter_depth(all_entries)
    chapter_entries = [e for e in all_entries if e[2] == chapter_depth]
    chapter_entries.sort(key=lambda e: e[1])

    total_pages = len(reader.pages)

    # Assign end_page for each chapter (exclusive)
    ranges = []
    for i, (title, start, _) in enumerate(chapter_entries):
        end = chapter_entries[i + 1][1] if i + 1 < len(chapter_entries) else total_pages
        if end <= start:
            end = start + 1
        ranges.append((title, start, end))

    # Book title from metadata, fallback to filename
    meta = reader.metadata
    title_raw = (meta.title if meta and meta.title else book_path.stem) or book_path.stem
    book_title = sanitize_book_title(title_raw)

    chapters_dir = output_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    chapters_meta = []
    for i, (title, start, end) in enumerate(ranges, 1):
        writer = pypdf.PdfWriter()
        body_length = 0
        for page_idx in range(start, end):
            page = reader.pages[page_idx]
            writer.add_page(page)
            try:
                body_length += len((page.extract_text() or "").strip())
            except Exception:
                pass
        slug = slugify(title)
        file_path = chapters_dir / f"ch{i:02d}_{slug}.pdf"
        with open(file_path, "wb") as f:
            writer.write(f)
        skip_recommended, skip_reason = compute_skip_recommended(title, body_length)
        chapters_meta.append({
            "index": i,
            "title": title.strip(),
            "slug": slug,
            "file_path": str(file_path.resolve()),
            "pages": [start, end],
            "body_length": body_length,
            "skip_recommended": skip_recommended,
            "skip_reason": skip_reason,
        })

    return {
        "book_title": book_title,
        "source_path": str(book_path.resolve()),
        "format": "pdf",
        "chapter_count": len(chapters_meta),
        "chapters": chapters_meta,
    }


# --------------------------------------------------------------------- EPUB


def _epub_flat_toc(toc):
    """Flatten ebooklib TOC. Yields (title, href) pairs."""
    for item in toc:
        if isinstance(item, tuple):
            section, subitems = item
            title = getattr(section, "title", None) or getattr(section, "__str__", lambda: "")()
            href = getattr(section, "href", "") or ""
            if title:
                yield (str(title).strip(), href.split("#")[0])
            yield from _epub_flat_toc(subitems)
        else:
            title = getattr(item, "title", "")
            href = getattr(item, "href", "") or ""
            if title:
                yield (str(title).strip(), href.split("#")[0])


def extract_epub_chapters(book_path: Path, output_dir: Path) -> dict:
    book = epub.read_epub(str(book_path), options={"ignore_ncx": False})

    title_meta = book.get_metadata("DC", "title")
    title_raw = title_meta[0][0] if title_meta else book_path.stem
    book_title = sanitize_book_title(title_raw)

    toc = book.toc
    if not toc:
        raise NoTOCError(
            f"EPUB 无目录 (nav/NCX) — {book_path.name}\n"
            f"建议：用 Calibre 重新转换该文件以生成目录。"
        )

    chapters_dir = output_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    seen_hrefs: set[str] = set()
    chapters_meta = []
    i = 0
    for chap_title, href in _epub_flat_toc(toc):
        if not href or href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        item = book.get_item_with_href(href)
        if item is None:
            continue

        html = item.get_content().decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n", strip=True)
        if not text.strip():
            continue

        i += 1
        slug = slugify(chap_title)
        file_path = chapters_dir / f"ch{i:02d}_{slug}.txt"
        header = f"{chap_title}\n{'=' * max(3, len(chap_title))}\n\n"
        file_path.write_text(header + text, encoding="utf-8")

        body_length = len(text.strip())
        skip_recommended, skip_reason = compute_skip_recommended(chap_title, body_length)
        chapters_meta.append({
            "index": i,
            "title": chap_title.strip(),
            "slug": slug,
            "file_path": str(file_path.resolve()),
            "body_length": body_length,
            "skip_recommended": skip_recommended,
            "skip_reason": skip_reason,
        })

    if not chapters_meta:
        raise NoTOCError(
            f"EPUB 有目录但所有章节内容为空 — {book_path.name}"
        )

    return {
        "book_title": book_title,
        "source_path": str(book_path.resolve()),
        "format": "epub",
        "chapter_count": len(chapters_meta),
        "chapters": chapters_meta,
    }


# ------------------------------------------------------------------ Errors


class NoTOCError(Exception):
    pass


# -------------------------------------------------------------------- Main


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1

    book_path = Path(argv[1]).expanduser().resolve()
    output_dir = Path(argv[2]).expanduser().resolve()

    if not book_path.exists():
        print(f"error: 文件不存在: {book_path}", file=sys.stderr)
        return 1

    suffix = book_path.suffix.lower()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if suffix == ".pdf":
            meta = extract_pdf_chapters(book_path, output_dir)
        elif suffix == ".epub":
            meta = extract_epub_chapters(book_path, output_dir)
        else:
            print(f"error: 不支持的格式 {suffix}（仅支持 .pdf / .epub）", file=sys.stderr)
            return 2
    except NoTOCError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"error: 解析失败: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    meta_path = output_dir / "chapters.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary JSON to stdout for Claude to consume
    print(json.dumps({
        "status": "ok",
        "book_title": meta["book_title"],
        "format": meta["format"],
        "chapter_count": meta["chapter_count"],
        "chapters_json": str(meta_path),
        "chapter_titles": [c["title"] for c in meta["chapters"]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
