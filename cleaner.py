import re


class TextCleaner:
    """
    Cleans raw extracted text while preserving document structure.
    Removes noise without losing meaningful content.
    """

    def clean(self, text: str) -> str:
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove null bytes and non-printable control characters (keep \n and \t)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Remove repeated special characters used as decorative separators
        text = re.sub(r"[-=_*]{4,}", "", text)

        # Collapse multiple spaces into one (preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse more than 2 consecutive newlines into 2 (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove lines that are pure whitespace or single characters (page numbers, etc.)
        lines = [line for line in lines if len(line) > 1 or line == ""]

        # Remove duplicate consecutive lines
        deduped = []
        for line in lines:
            if not deduped or line != deduped[-1]:
                deduped.append(line)

        return "\n".join(deduped).strip()
