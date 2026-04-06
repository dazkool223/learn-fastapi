Create an books application

Create an in-memory data structure of books and support the following endpoints

| Method | Endpoint         | Description       | Parameters                          | Returns                     |
| ------ | ---------------- | ----------------- | ----------------------------------- | --------------------------- |
| GET    | `/books`         | Get all books     | None                                | List of all books           |
| GET    | `/books/{index}` | Get book by index | `index` (path)                      | Single book                 |
| POST   | `/books`         | Add new book      | `book_name` (query)                 | Confirmation + book         |
| PUT    | `/books/{index}` | Update book       | `index` (path), `book_name` (query) | Confirmation + updated book |
| DELETE | `/books/{index}` | Delete book       | `index` (path)                      | Confirmation + deleted book |
