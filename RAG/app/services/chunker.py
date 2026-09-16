import re


def clean_text(text: str) -> str:
    """
    Basic text cleaning before chunking.

    We don't do anything fancy here (no stopword removal, no stemming) -
    the embedding model was trained on natural text, so over-cleaning
    would only throw away information it could use. We just remove
    control characters and collapse repeated whitespace so chunk
    boundaries land on sensible spots.
    """
    if not text:
        return ""

    # Drop null bytes / control characters that sometimes leak out of PDFs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)

    # Collapse any run of whitespace (spaces, tabs, newlines) into one space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Split text into overlapping, fixed-size character chunks.

    Why character-based instead of sentence/paragraph splitting?
    It's simple, predictable, and works the same for every document
    type/language without extra NLP dependencies. The overlap makes
    sure that an idea sitting right at a chunk boundary still appears
    fully in at least one chunk.

    Example with chunk_size=1000, chunk_overlap=150:
        chunk 1: characters [0:1000]
        chunk 2: characters [850:1850]
        chunk 3: characters [1700:2700]
        ...
    """
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = clean_text(text)
    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]

        # Avoid cutting a word in half at the end of a chunk, unless we're
        # already at the end of the document.
        if end < text_length:
            last_space = chunk.rfind(" ")
            if last_space > chunk_size * 0.5:  # only trim if it's not too wasteful
                end = start + last_space
                chunk = text[start:end]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks
