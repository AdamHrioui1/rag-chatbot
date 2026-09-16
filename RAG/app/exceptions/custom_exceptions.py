class RAGException(Exception):
    """Base exception for the application"""

    pass


class DeepSeekException(RAGException):
    """Raised when deepseek fails"""

    pass


class RetrievalException(RAGException):
    """Raised when retrieval failed"""

    pass


class UnsupportedFileTypeException(RAGException):
    """Raised when an uploaded file's extension isn't one we support"""

    pass


class FileTooLargeException(RAGException):
    """Raised when an uploaded file exceeds the configured size limit"""

    pass


class DocumentExtractionException(RAGException):
    """Raised when we can't extract readable text from a file (corrupted,
    empty, password-protected, etc.)"""

    pass


class InvalidZipException(RAGException):
    """Raised when a ZIP file is corrupted or fails safety checks
    (e.g. path traversal attempt, no supported files inside)"""

    pass