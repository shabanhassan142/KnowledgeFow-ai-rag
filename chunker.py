from typing import List
from dataclasses import dataclass, field
from app.rag.extractors import ExtractedPage
from app.core.config import settings


@dataclass
class TextChunk:
    """A single chunk ready for embedding."""
    content: str
    chunk_index: int
    page_number: int
    section_heading: str
    token_count: int
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    """
    Splits extracted pages into overlapping chunks using a
    recursive character-based strategy via LangChain.
    Chunk size and overlap are pulled from settings (configurable).
    """

    def __init__(self):
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk_pages(self, pages: List[ExtractedPage]) -> List[TextChunk]:
        """Chunk all pages of a document, preserving page and section metadata."""
        chunks: List[TextChunk] = []
        chunk_index = 0

        for page in pages:
            if not page.content.strip():
                continue

            splits = self.splitter.split_text(page.content)
            section_heading = page.metadata.get("section_heading", "")

            for split in splits:
                if not split.strip():
                    continue
                chunks.append(TextChunk(
                    content=split.strip(),
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                    section_heading=section_heading,
                    token_count=self._estimate_tokens(split),
                    metadata=page.metadata,
                ))
                chunk_index += 1

        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token (OpenAI approximation)."""
        return max(1, len(text) // 4)
