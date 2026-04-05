from fastapi import HTTPException, status

class LibraryException(HTTPException):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"
    
    def __init__(self, detail : str | None = None) :
        super().__init__(
            status_code= self.status_code,
            detail=self.detail
        )

class BookNotFoundException(LibraryException) :
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Book not found."

class DuplicateISBNException(LibraryException):
    status_code = status.HTTP_409_CONFLICT
    
    def __init__(self, detail):
        super().__init__(
            detail=detail
        )

