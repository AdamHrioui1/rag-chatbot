import io
import logging
import zipfile

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.config import settings
from app.exceptions.custom_exceptions import (
    DocumentExtractionException,
    InvalidZipException,
    UnsupportedFileTypeException,
)

logger = logging.getLogger(__name__)

# Safety limits for ZIP uploads - these protect the server against
# "zip bombs" (a tiny file that decompresses into gigabytes of data)
# and against a ZIP containing an unreasonable number of files.
MAX_FILES_IN_ZIP = 20
MAX_ZIP_UNCOMPRESSED_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024 * MAX_FILES_IN_ZIP


def get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def extract_text(filename: str, content: bytes) -> str:
    """
    Pull raw text out of a single (non-zip) file.
    Dispatches by extension - keeps each format's quirks isolated.
    """
    extension = get_extension(filename)

    if extension == ".txt":
        return _extract_txt(content)
    if extension == ".pdf":
        return _extract_pdf(content)
    if extension == ".docx":
        return _extract_docx(content)

    raise UnsupportedFileTypeException(
        f"'{extension}' is not a supported file type. "
        f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    )


def _extract_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        # Some plain text files aren't UTF-8 (older Windows exports, etc.)
        # Fall back instead of failing outright.
        return content.decode("latin-1", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))

        if reader.is_encrypted:
            raise DocumentExtractionException(
                "This PDF is password-protected and can't be read."
            )

        pages_text = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages_text)

        if not text.strip():
            raise DocumentExtractionException(
                "No readable text found in this PDF "
                "(it may be a scanned image without OCR text)."
            )

        return text
    except DocumentExtractionException:
        raise
    except Exception as e:
        logger.warning(f"Failed to parse PDF: {e}")
        raise DocumentExtractionException(
            "This PDF file appears to be corrupted and could not be read."
        ) from e


def _extract_docx(content: bytes) -> str:
    try:
        document = DocxDocument(io.BytesIO(content))
        paragraphs = [p.text for p in document.paragraphs]
        text = "\n".join(paragraphs)

        if not text.strip():
            raise DocumentExtractionException("This DOCX file has no readable text.")

        return text
    except DocumentExtractionException:
        raise
    except Exception as e:
        logger.warning(f"Failed to parse DOCX: {e}")
        raise DocumentExtractionException(
            "This DOCX file appears to be corrupted and could not be read."
        ) from e


def extract_files_from_zip(content: bytes) -> list[tuple[str, bytes]]:
    """
    Safely read the supported files out of a ZIP archive, in memory.

    Security notes:
    - We never call `ZipFile.extractall()` and never write using the
      archive's own paths, which is what makes "zip-slip" path traversal
      attacks (a member named e.g. "../../etc/passwd") possible. Instead
      we read each member's bytes into memory and only keep the
      basename of its filename - the caller then saves it under our own
      generated safe name.
    - We reject archives that are too big (uncompressed) or contain too
      many files, to avoid a small ZIP expanding into a huge one
      ("zip bomb").
    """
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as e:
        raise InvalidZipException("This ZIP file is corrupted and could not be opened.") from e

    infos = [info for info in zip_file.infolist() if not info.is_dir()]

    if len(infos) == 0:
        raise InvalidZipException("This ZIP file is empty.")

    if len(infos) > MAX_FILES_IN_ZIP:
        raise InvalidZipException(
            f"This ZIP contains too many files (max {MAX_FILES_IN_ZIP})."
        )

    total_size = sum(info.file_size for info in infos)
    if total_size > MAX_ZIP_UNCOMPRESSED_BYTES:
        raise InvalidZipException("This ZIP file is too large once decompressed.")

    extracted: list[tuple[str, bytes]] = []
    skipped: list[str] = []

    for info in infos:
        # Take only the filename, discarding any directory path - this is
        # what neutralizes path traversal attempts like "../../evil.txt".
        safe_name = info.filename.replace("\\", "/").split("/")[-1]

        if not safe_name:
            continue

        extension = get_extension(safe_name)
        if extension not in settings.ALLOWED_EXTENSIONS:
            skipped.append(safe_name)
            continue

        extracted.append((safe_name, zip_file.read(info)))

    if not extracted:
        raise InvalidZipException(
            "No supported files (.pdf, .docx, .txt) were found inside this ZIP."
        )

    if skipped:
        logger.info(f"Skipped unsupported files inside ZIP: {skipped}")

    return extracted
