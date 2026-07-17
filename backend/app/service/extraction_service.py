from typing import Optional
import io
import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import openpyxl
from pptx import Presentation


async def extract_text(file_path: str, file_type: str, content: bytes) -> tuple[str, Optional[int]]:
    if "pdf" in file_type:
        return extract_pdf(content)
    elif "wordprocessingml" in file_type or "docx" in file_type:
        return extract_docx(content)
    elif "spreadsheetml" in file_type or "xlsx" in file_type:
        return extract_xlsx(content)
    elif "presentationml" in file_type or "pptx" in file_type:
        return extract_pptx(content)
    elif "html" in file_type:
        return extract_html(content)
    elif "xml" in file_type:
        return extract_xml(content)
    elif "markdown" in file_type:
        return extract_markdown(content)
    else:
        return content.decode("utf-8"), None


def extract_pdf(content: bytes) -> tuple[str, Optional[int]]:
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages), len(reader.pages)


def extract_docx(content: bytes) -> tuple[str, Optional[int]]:
    doc = docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs), None


def extract_xlsx(content: bytes) -> tuple[str, Optional[int]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f"\n## Sheet: {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            lines.append(" | ".join(str(c) if c is not None else "" for c in row))
    return "\n".join(lines), None


def extract_pptx(content: bytes) -> tuple[str, Optional[int]]:
    prs = Presentation(io.BytesIO(content))
    lines = []
    for i, slide in enumerate(prs.slides):
        lines.append(f"\n## Slide {i + 1}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                lines.append(shape.text)
    return "\n".join(lines), len(prs.slides)


def extract_html(content: bytes) -> tuple[str, Optional[int]]:
    return BeautifulSoup(content, "html.parser").get_text(separator="\n", strip=True), None


def extract_xml(content: bytes) -> tuple[str, Optional[int]]:
    return BeautifulSoup(content, "xml").get_text(separator="\n", strip=True), None


def extract_markdown(content: bytes) -> tuple[str, Optional[int]]:
    html = markdown.markdown(content.decode("utf-8"))
    return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True), None
