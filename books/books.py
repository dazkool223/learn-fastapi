from fastapi import FastAPI

app = FastAPI()

books = []

@app.get("/")
def hello() :
    return "Hello"

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