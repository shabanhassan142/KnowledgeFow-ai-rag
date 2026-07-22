from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    """Represents a single page or logical section from a document."""
    page_number: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> List[ExtractedPage]:
        """Extract text from a file, returning a list of pages/sections."""
        ...


class PDFExtractor(BaseExtractor):
    """Extracts text from PDF files using PyMuPDF."""

    def extract(self, file_path: str) -> List[ExtractedPage]:
        import fitz  # PyMuPDF

        pages = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text.strip():
                    pages.append(ExtractedPage(
                        page_number=page_num,
                        content=text,
                        metadata={"total_pages": len(doc)},
                    ))
        return pages


class DOCXExtractor(BaseExtractor):
    """Extracts text from DOCX files using python-docx."""

    def extract(self, file_path: str) -> List[ExtractedPage]:
        from docx import Document

        doc = Document(file_path)
        sections: List[ExtractedPage] = []
        current_heading = ""
        current_lines: List[str] = []
        section_index = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            is_heading = para.style.name.startswith("Heading")

            if is_heading:
                # Flush previous section
                if current_lines:
                    sections.append(ExtractedPage(
                        page_number=section_index,
                        content="\n".join(current_lines),
                        metadata={"section_heading": current_heading},
                    ))
                    section_index += 1
                    current_lines = []
                current_heading = text
            else:
                current_lines.append(text)

        # Flush last section
        if current_lines:
            sections.append(ExtractedPage(
                page_number=section_index,
                content="\n".join(current_lines),
                metadata={"section_heading": current_heading},
            ))

        return sections


class TXTExtractor(BaseExtractor):
    """Extracts text from plain text files."""

    def extract(self, file_path: str) -> List[ExtractedPage]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return [ExtractedPage(page_number=1, content=content)]


class MarkdownExtractor(BaseExtractor):
    """Extracts text from Markdown files, stripping markdown syntax."""

    def extract(self, file_path: str) -> List[ExtractedPage]:
        import re

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Strip markdown syntax for clean plain text
        content = re.sub(r"#{1,6}\s*", "", content)   # headings
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)  # bold
        content = re.sub(r"\*(.+?)\*", r"\1", content)       # italic
        content = re.sub(r"`{1,3}[^`]*`{1,3}", "", content)  # code
        content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content) # links
        content = re.sub(r"!\[.*?\]\(.+?\)", "", content)     # images

        return [ExtractedPage(page_number=1, content=content)]


def get_extractor(file_type: str) -> BaseExtractor:
    """Factory — returns the correct extractor for a given file type."""
    extractors = {
        "pdf":  PDFExtractor(),
        "docx": DOCXExtractor(),
        "txt":  TXTExtractor(),
        "md":   MarkdownExtractor(),
    }
    extractor = extractors.get(file_type.lower())
    if not extractor:
        raise ValueError(f"No extractor available for file type: {file_type}")
    return extractor
