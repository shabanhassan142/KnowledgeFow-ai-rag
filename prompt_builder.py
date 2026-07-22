from typing import List, Dict, Any

SYSTEM_PROMPT = """You are an intelligent, professional AI Assistant for a company's internal knowledge base.

INSTRUCTIONS:
- Answer the user's question clearly and accurately using the provided document excerpts.
- Cite the source document name (and page/section if available).
- If the user greets you or asks what documents exist, list the Available Knowledge Base Documents.
- Be polite, helpful, concise, and accurate.
"""


def build_context_block(chunks: List[Dict[str, Any]], available_docs: List[str] = None) -> str:
    """Format retrieved chunks and available document list for the prompt."""
    lines = []

    if available_docs:
        lines.append("AVAILABLE KNOWLEDGE BASE DOCUMENTS:")
        for doc in available_docs:
            lines.append(f"- {doc}")
        lines.append("")

    if chunks:
        lines.append("RELEVANT DOCUMENT EXCERPTS:")
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata", {})
            source = meta.get("document_name", "Unknown document")
            page = meta.get("page_number", "")
            section = meta.get("section_heading", "")

            header_parts = [f"Excerpt {i} (Source: {source}"]
            if page:
                header_parts.append(f"Page: {page}")
            if section:
                header_parts.append(f"Section: {section}")
            header_parts[-1] += ")"

            lines.append(" | ".join(header_parts))
            lines.append(chunk["content"].strip())
            lines.append("")

    return "\n".join(lines)


def build_messages(
    question: str,
    context_chunks: List[Dict[str, Any]],
    conversation_history: List[Dict[str, str]],
    available_docs: List[str] = None,
) -> List[Dict[str, str]]:
    """Build the full messages list for LLM call."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject conversation memory
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Build context block containing active doc list + retrieved excerpts
    context_block = build_context_block(context_chunks, available_docs)
    user_content = f"Please use the following company information to answer the question:\n\n{context_block}\nUser Question: {question}"
    messages.append({"role": "user", "content": user_content})

    return messages
