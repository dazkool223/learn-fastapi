## Books API

### Purpose

The Books API demonstrates complete CRUD (Create, Read, Update, Delete) operations, which form the foundation of most REST APIs.

### Endpoints

| Method | Endpoint         | Description       | Parameters                          | Returns                     |
| ------ | ---------------- | ----------------- | ----------------------------------- | --------------------------- |
| GET    | `/books`         | Get all books     | None                                | List of all books           |
| GET    | `/books/{index}` | Get book by index | `index` (path)                      | Single book                 |
| POST   | `/books`         | Add new book      | `book_name` (query)                 | Confirmation + book         |
| PUT    | `/books/{index}` | Update book       | `index` (path), `book_name` (query) | Confirmation + updated book |
| DELETE | `/books/{index}` | Delete book       | `index` (path)                      | Confirmation + deleted book |

### Code Structure

```python
from fastapi import FastAPI

app = FastAPI()

books = []  # In-memory list to store books

@app.get("/books")
def get_all_books():
    return {"books": books}

@app.get("/books/{index}")
def get_book(index: int):
    return {"book": books[index]}

@app.post("/books")
def create_book(book_name: str):
    books.append(book_name)
    return {"message": "Book added", "book": book_name}

@app.put("/books/{index}")
def update_book(index: int, book_name: str):
    books[index] = book_name
    return {"message": "Book updated", "book": book_name}

@app.delete("/books/{index}")
def delete_book(index: int):
    deleted_book = books.pop(index)
    return {"message": "Book deleted", "book": deleted_book}
```

### Key Concepts

**CRUD Operations**: The four basic operations for persistent storage:
- **Create** (POST): Add new books
- **Read** (GET): Retrieve books
- **Update** (PUT): Modify existing books
- **Delete** (DELETE): Remove books

**Path Parameters**: `{index}` in the URL is a path parameter that FastAPI automatically parses and passes to your function.

**Query Parameters**: `book_name` is passed as a query parameter in the URL like `?book_name=Python`.

**In-Memory Storage**: Books are stored in a Python list, which is simple but not persistent.

### Usage Examples

**Starting the server:**
```bash
uvicorn books_api:app --reload
```

### Understanding the Flow

**Creating a Book:**
1. Client sends POST request with book name
2. Server appends book to the list
3. Server responds with success message

**Reading Books:**
1. Client sends GET request
2. Server returns current list or specific book
3. No changes are made to data

**Updating a Book:**
1. Client sends PUT request with index and new name
2. Server replaces book at that index
3. Server responds with updated book

**Deleting a Book:**
1. Client sends DELETE request with index
2. Server removes book from list
3. Server responds with deleted book

### Real-World Extensions

This basic API can be extended to:

**Add More Fields:**
```python
books = [
    {"id": 1, "title": "Python Basics", "author": "John Doe", "year": 2023},
    {"id": 2, "title": "FastAPI Guide", "author": "Jane Smith", "year": 2024}
]
```

**Add Search/Filter:**
```python
@app.get("/books/search")
def search_books(author: str):
    return [b for b in books if b["author"] == author]
```

**Add Validation:**
Check if index exists, validate input format, ensure unique titles.

**Use Database:**
Replace the list with SQLite, PostgreSQL, or MongoDB for persistence.

## Next Steps

After mastering these examples, explore:
- Database integration (SQLAlchemy)
- Request validation (Pydantic models)
- Error handling and custom exceptions
- Authentication and authorization
- Testing your APIs
- API documentation with Swagger
- Deployment to production serve