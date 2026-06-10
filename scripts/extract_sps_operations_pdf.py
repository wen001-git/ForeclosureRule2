from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = PROJECT_ROOT / "SPS Operations.pdf"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "SPS_Operations_extracted"
ASSET_DIR = OUTPUT_DIR / "assets"
MD_PATH = OUTPUT_DIR / "SPS_Operations.md"
HTML_PATH = OUTPUT_DIR / "SPS_Operations_reader.html"


@dataclass
class ImageOccurrence:
    page: int
    index: int
    source_name: str
    asset_name: str
    width: int | None
    height: int | None
    byte_count: int
    digest: str


@dataclass
class PageData:
    number: int
    text: str
    images: list[ImageOccurrence]


def slug_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return safe or "image"


def guess_extension(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".jp2"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".bin"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def rel_asset(asset_name: str) -> str:
    return f"assets/{asset_name}"


def write_image_asset(asset_name: str, data: bytes) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    target = ASSET_DIR / asset_name
    target.write_bytes(data)


def extract_pdf() -> tuple[list[PageData], dict[str, str]]:
    reader = PdfReader(str(PDF_PATH))
    digest_to_asset: dict[str, str] = {}
    pages: list[PageData] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        occurrences: list[ImageOccurrence] = []

        for image_index, image_file in enumerate(getattr(page, "images", []), start=1):
            data = image_file.data or b""
            digest = hashlib.sha256(data).hexdigest()
            extension = guess_extension(image_file.name)
            if digest not in digest_to_asset:
                asset_name = (
                    f"p{page_number:03d}_img{image_index:02d}_"
                    f"{digest[:10]}{extension}"
                )
                write_image_asset(asset_name, data)
                digest_to_asset[digest] = asset_name

            pil_image = getattr(image_file, "image", None)
            width: int | None = None
            height: int | None = None
            if pil_image is not None:
                width, height = pil_image.size

            occurrences.append(
                ImageOccurrence(
                    page=page_number,
                    index=image_index,
                    source_name=image_file.name,
                    asset_name=digest_to_asset[digest],
                    width=width,
                    height=height,
                    byte_count=len(data),
                    digest=digest,
                )
            )

        pages.append(PageData(number=page_number, text=text, images=occurrences))

    metadata = {
        "source_pdf": PDF_PATH.name,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "page_count": str(len(pages)),
        "image_occurrence_count": str(sum(len(page.images) for page in pages)),
        "unique_image_count": str(len(digest_to_asset)),
        "total_text_chars": str(sum(len(page.text) for page in pages)),
    }
    return pages, metadata


def markdown_header(metadata: dict[str, str]) -> str:
    return f"""# SPS Operations Extracted Reading Notes

## Document Purpose

- **Why this document exists**: Extract the readable text and embedded image assets from `SPS Operations.pdf` into a format that is easier for AI analysis, manual browsing, and note-taking.
- **What problem it solves**: The original PDF is harder to search, quote, annotate, and feed into AI tools. This Markdown file provides a page-by-page text and image index.
- **Scope**: Covers extracted PDF text, page-level organization, extracted embedded images, and note placeholders. It does not claim OCR correction or legal/business interpretation.
- **System fit**: Supports the ForeclosureRule2 project by turning a source PDF into a durable local analysis artifact.

## Target Audience

Primary readers: developers, data engineers, business analysts, validators, operations teams, reviewers, future AI sessions.

Secondary readers: onboarding engineers, architects, and anyone reviewing SPS operational references.

## Revision History

| Date | Author | Version | Changes | Related |
|------|--------|---------|---------|---------|
| 2026-06-09 | AI Agent | v1 | Initial PDF extraction to Markdown and HTML reader | `SPS Operations.pdf` |

## Dependencies

- Source PDF: `../../SPS Operations.pdf`
- Image assets: `assets/`
- Generated UTC: {metadata["generated_utc"]}

## Known Limitations

- The PDF pages are rotated; this extraction uses the standard `pypdf` text layer extraction because layout-mode extraction returned incomplete output.
- Extracted image assets are embedded PDF image objects, not full-page rendered screenshots.
- Some tiny extracted images may be line or layout artifacts from the PDF rather than business diagrams.

## Extraction Summary

| Metric | Value |
|--------|------:|
| Pages | {metadata["page_count"]} |
| Text characters | {metadata["total_text_chars"]} |
| Image occurrences | {metadata["image_occurrence_count"]} |
| Unique image assets | {metadata["unique_image_count"]} |

"""


def image_dimension_text(image: ImageOccurrence) -> str:
    if image.width is None or image.height is None:
        return "unknown"
    return f"{image.width} x {image.height}"


def write_markdown(pages: Iterable[PageData], metadata: dict[str, str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [markdown_header(metadata)]

    for page in pages:
        lines.append(f"## Page {page.number}\n")
        lines.append("### Extracted Text\n")
        if page.text:
            lines.append("```text\n" + page.text + "\n```\n")
        else:
            lines.append("_No extractable text found on this page._\n")

        lines.append("### Extracted Images\n")
        if page.images:
            lines.append("| # | Source object | Dimensions | Bytes | Asset |\n")
            lines.append("|---:|---------------|------------|------:|-------|\n")
            for image in page.images:
                asset = rel_asset(image.asset_name)
                lines.append(
                    f"| {image.index} | `{image.source_name}` | "
                    f"{image_dimension_text(image)} | {image.byte_count} | "
                    f"[{image.asset_name}]({asset}) |\n"
                )
            lines.append("\n")
            for image in page.images:
                if image.width and image.height and image.width >= 24 and image.height >= 24:
                    alt = f"Page {page.number} image {image.index}"
                    lines.append(f"![{alt}]({rel_asset(image.asset_name)})\n")
        else:
            lines.append("_No embedded images found on this page._\n")

        lines.append("### Notes\n")
        lines.append("- \n\n")

    MD_PATH.write_text("".join(lines), encoding="utf-8")


def html_header(metadata: dict[str, str]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SPS Operations Reader</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202124;
      --muted: #5f6368;
      --line: #d6d9dc;
      --panel: #ffffff;
      --soft: #f4f7f9;
      --accent: #136f63;
      --accent-2: #7a4e12;
      --focus: #e6f2ef;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 15px/1.55 "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: #f7f8fa;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
      min-height: 100vh;
    }}
    nav {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 22px 18px;
      border-right: 1px solid var(--line);
      background: #eef2f3;
    }}
    nav h1 {{
      margin: 0 0 16px;
      font-size: 20px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    nav .meta {{
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 13px;
    }}
    nav ol {{
      margin: 0;
      padding-left: 21px;
    }}
    nav li {{
      margin: 6px 0;
    }}
    main {{
      padding: 26px clamp(18px, 3vw, 42px) 48px;
    }}
    .doc-header, .page {{
      max-width: 1120px;
      margin: 0 auto 20px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
      box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }}
    .doc-header h2, .page h2 {{
      margin: 0 0 12px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 22px 0 8px;
      font-size: 16px;
      letter-spacing: 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
      margin: 16px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 12px;
      background: var(--soft);
    }}
    .metric strong {{
      display: block;
      font-size: 20px;
      color: var(--accent);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 16px;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 7px 8px;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #edf3f1;
      font-weight: 600;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      margin: 8px 0 14px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbfc;
      font: 13px/1.5 Consolas, "Cascadia Mono", monospace;
    }}
    .image-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 10px;
    }}
    figure {{
      margin: 0;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbfc;
    }}
    figure img {{
      display: block;
      max-width: 100%;
      max-height: 260px;
      margin: 0 auto 8px;
      object-fit: contain;
      background: white;
      border: 1px solid #e6e8ea;
    }}
    figcaption {{
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    textarea {{
      width: 100%;
      min-height: 120px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: 14px/1.45 "Segoe UI", Arial, sans-serif;
      background: #fffef8;
    }}
    .toolbar {{
      max-width: 1120px;
      margin: 0 auto 20px;
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    button {{
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 8px 12px;
      font: inherit;
      cursor: pointer;
    }}
    button.secondary {{
      background: white;
      color: var(--accent);
    }}
    .status {{
      color: var(--muted);
      font-size: 13px;
    }}
    .small {{
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      main {{ padding: 18px 12px 32px; }}
      .doc-header, .page {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
<div class="layout">
"""


def html_doc_header(metadata: dict[str, str]) -> str:
    return f"""
  <nav>
    <h1>SPS Operations Reader</h1>
    <p class="meta">Generated {html.escape(metadata["generated_utc"])}<br>
    Source: <a href="../../SPS%20Operations.pdf">SPS Operations.pdf</a></p>
    <ol>
      {"".join(f'<li><a href="#page-{i}">Page {i}</a></li>' for i in range(1, int(metadata["page_count"]) + 1))}
    </ol>
  </nav>
  <main>
    <section class="doc-header" id="top">
      <h2>Document Purpose</h2>
      <p><strong>Why this document exists:</strong> Extract the readable text and embedded image assets from <code>SPS Operations.pdf</code> into a format that is easier for AI analysis, manual browsing, and note-taking.</p>
      <p><strong>What problem it solves:</strong> The original PDF is harder to search, quote, annotate, and feed into AI tools. This reader keeps the content page-by-page and adds local note areas.</p>
      <p><strong>Scope:</strong> Covers extracted PDF text, page-level organization, extracted embedded images, and note placeholders. It does not claim OCR correction or legal/business interpretation.</p>
      <p><strong>System fit:</strong> Supports the ForeclosureRule2 project by turning a source PDF into a durable local analysis artifact.</p>

      <h3>Target Audience</h3>
      <p>Primary readers: developers, data engineers, business analysts, validators, operations teams, reviewers, future AI sessions. Secondary readers: onboarding engineers, architects, and anyone reviewing SPS operational references.</p>

      <h3>Revision History</h3>
      <table>
        <thead><tr><th>Date</th><th>Author</th><th>Version</th><th>Changes</th><th>Related</th></tr></thead>
        <tbody><tr><td>2026-06-09</td><td>AI Agent</td><td>v1</td><td>Initial PDF extraction to Markdown and HTML reader</td><td><code>SPS Operations.pdf</code></td></tr></tbody>
      </table>

      <h3>Dependencies</h3>
      <p>Source PDF: <code>../../SPS Operations.pdf</code>. Image assets: <code>assets/</code>.</p>

      <h3>Known Limitations</h3>
      <ul>
        <li>The PDF pages are rotated; this extraction uses the standard <code>pypdf</code> text layer extraction because layout-mode extraction returned incomplete output.</li>
        <li>Extracted image assets are embedded PDF image objects, not full-page rendered screenshots.</li>
        <li>Some tiny extracted images may be line or layout artifacts from the PDF rather than business diagrams.</li>
      </ul>

      <h3>Extraction Summary</h3>
      <div class="summary">
        <div class="metric"><strong>{metadata["page_count"]}</strong> Pages</div>
        <div class="metric"><strong>{metadata["total_text_chars"]}</strong> Text characters</div>
        <div class="metric"><strong>{metadata["image_occurrence_count"]}</strong> Image occurrences</div>
        <div class="metric"><strong>{metadata["unique_image_count"]}</strong> Unique image assets</div>
      </div>
    </section>
    <div class="toolbar">
      <button type="button" id="export-notes">Export notes as Markdown</button>
      <button type="button" id="clear-notes" class="secondary">Clear saved notes</button>
      <span class="status" id="status">Notes autosave in this browser for this file path.</span>
    </div>
"""


def write_html(pages: Iterable[PageData], metadata: dict[str, str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parts: list[str] = [html_header(metadata), html_doc_header(metadata)]

    for page in pages:
        parts.append(f'<section class="page" id="page-{page.number}">\n')
        parts.append(f"  <h2>Page {page.number}</h2>\n")
        parts.append("  <h3>Extracted Text</h3>\n")
        if page.text:
            parts.append(f"  <pre>{html.escape(page.text)}</pre>\n")
        else:
            parts.append('  <p class="small">No extractable text found on this page.</p>\n')

        parts.append("  <h3>Extracted Images</h3>\n")
        if page.images:
            parts.append("  <table>\n")
            parts.append("    <thead><tr><th>#</th><th>Source object</th><th>Dimensions</th><th>Bytes</th><th>Asset</th></tr></thead>\n")
            parts.append("    <tbody>\n")
            for image in page.images:
                asset = rel_asset(image.asset_name)
                parts.append(
                    "      <tr>"
                    f"<td>{image.index}</td>"
                    f"<td><code>{html.escape(image.source_name)}</code></td>"
                    f"<td>{html.escape(image_dimension_text(image))}</td>"
                    f"<td>{image.byte_count}</td>"
                    f'<td><a href="{html.escape(asset)}">{html.escape(image.asset_name)}</a></td>'
                    "</tr>\n"
                )
            parts.append("    </tbody>\n")
            parts.append("  </table>\n")
            parts.append('  <div class="image-grid">\n')
            for image in page.images:
                if image.width and image.height and image.width >= 24 and image.height >= 24:
                    asset = rel_asset(image.asset_name)
                    caption = (
                        f"Image {image.index}, {image_dimension_text(image)}, "
                        f"{image.byte_count} bytes"
                    )
                    parts.append(
                        "    <figure>"
                        f'<a href="{html.escape(asset)}"><img src="{html.escape(asset)}" alt="Page {page.number} image {image.index}"></a>'
                        f"<figcaption>{html.escape(caption)}</figcaption>"
                        "</figure>\n"
                    )
            parts.append("  </div>\n")
        else:
            parts.append('  <p class="small">No embedded images found on this page.</p>\n')

        parts.append("  <h3>Notes</h3>\n")
        parts.append(
            f'  <textarea data-page="{page.number}" '
            f'placeholder="Page {page.number} notes"></textarea>\n'
        )
        parts.append("</section>\n")

    notes_script = {
        "source": metadata["source_pdf"],
        "generated": metadata["generated_utc"],
        "pages": int(metadata["page_count"]),
    }
    parts.append(
        f"""
  </main>
</div>
<script>
const readerMeta = {json.dumps(notes_script)};
const notePrefix = 'sps-operations-notes::' + location.pathname + '::';
const statusEl = document.getElementById('status');
function setStatus(text) {{
  statusEl.textContent = text;
}}
for (const area of document.querySelectorAll('textarea[data-page]')) {{
  const key = notePrefix + area.dataset.page;
  area.value = localStorage.getItem(key) || '';
  area.addEventListener('input', () => {{
    localStorage.setItem(key, area.value);
    setStatus('Saved note for page ' + area.dataset.page + '.');
  }});
}}
document.getElementById('export-notes').addEventListener('click', () => {{
  const lines = [
    '# SPS Operations Notes',
    '',
    '- Source: ' + readerMeta.source,
    '- Exported: ' + new Date().toISOString(),
    ''
  ];
  for (const area of document.querySelectorAll('textarea[data-page]')) {{
    const value = area.value.trim();
    if (value) {{
      lines.push('## Page ' + area.dataset.page, '', value, '');
    }}
  }}
  const blob = new Blob([lines.join('\\n')], {{ type: 'text/markdown;charset=utf-8' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'SPS_Operations_notes.md';
  link.click();
  URL.revokeObjectURL(url);
  setStatus('Exported notes Markdown.');
}});
document.getElementById('clear-notes').addEventListener('click', () => {{
  if (!confirm('Clear notes saved for this reader file?')) return;
  for (const area of document.querySelectorAll('textarea[data-page]')) {{
    localStorage.removeItem(notePrefix + area.dataset.page);
    area.value = '';
  }}
  setStatus('Cleared saved notes.');
}});
</script>
</body>
</html>
"""
    )
    HTML_PATH.write_text("".join(parts), encoding="utf-8")


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)

    pages, metadata = extract_pdf()
    write_markdown(pages, metadata)
    write_html(pages, metadata)
    print(json.dumps(
        {
            "markdown": str(MD_PATH),
            "html": str(HTML_PATH),
            "assets": str(ASSET_DIR),
            **metadata,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
