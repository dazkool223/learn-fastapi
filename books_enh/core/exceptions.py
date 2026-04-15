from fastapi import HTTPException, status

# Base Exception

class LibraryException(HTTPException):
    """Base class for all library exceptions."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
        )


# Not Found Exception

class BookNotFoundException(LibraryException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Book not found"


class MemberNotFoundException(LibraryException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Member not found"


class LoanNotFoundException(LibraryException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Loan not found"


# Conflict Exception

class DuplicateISBNException(LibraryException):
    status_code = status.HTTP_409_CONFLICT
    detail = "A book with this ISBN already exists"


class DuplicateEmailException(LibraryException):
    status_code = status.HTTP_409_CONFLICT
    detail = "A member with this email already exists"


class BookAlreadyBorrowedException(LibraryException):
    status_code = status.HTTP_409_CONFLICT
    detail = "This member already has this book on loan"


class NoAvailableCopiesException(LibraryException):
    status_code = status.HTTP_409_CONFLICT
    detail = "No copies of this book are currently available"


# Bad Request Exception

class BookAlreadyReturnedException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "This book has already been returned"


class InactiveMemberException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Inactive members cannot borrow books"


class BookOnLoanException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Cannot perform this action while copies are on loan"


class InvalidCopiesException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Cannot reduce total copies below the number currently on loan"


class LoanPeriodExceededException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Requested loan period exceeds the maximum allowed"


class MemberDeactivatedException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Cannot deactivate a member with active loans"


# File Validation Exceptions

class InvalidFileExtensionException(LibraryException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "File extension is not allowed"


class InvalidMimeTypeException(LibraryException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "File MIME type is not allowed"


class FileTooLargeException(LibraryException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    detail = "File exceeds the maximum allowed size"


class BookFileNotFoundException(LibraryException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No file has been uploaded for this book"


# Storage Exception

class StorageUploadException(LibraryException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Failed to upload file to storage"


class StorageDeleteException(LibraryException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Failed to delete file from storage"


class DatabaseConnectionException(LibraryException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Could not connect to the database"


# LLM / Chat Exceptions

class LLMProviderException(LibraryException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "LLM provider returned an error"


class LLMRateLimitException(LibraryException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "LLM rate limit exceeded — please try again later"


class LLMTimeoutException(LibraryException):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    detail = "LLM request timed out"


class LLMConfigurationException(LibraryException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "LLM is not configured correctly"


class UnsupportedLLMProviderException(LibraryException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Unsupported LLM provider"
