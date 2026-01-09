# REST API Basics

## What is an API?

API stands for Application Programming Interface. It's a way for different software applications to communicate with each other. Think of it as a waiter in a restaurant: you (the client) tell the waiter (the API) what you want, and the waiter brings your request to the kitchen (the server) and returns with your food (the response).

## What is REST?

REST stands for Representational State Transfer. It's an architectural style for designing networked applications. A RESTful API uses HTTP requests to perform operations on data.

### Key Principles of REST

1. **Client-Server Architecture**: The client and server are separate, allowing them to evolve independently
2. **Stateless**: Each request from client to server must contain all information needed to understand the request
3. **Uniform Interface**: A consistent way to interact with resources using standard HTTP methods

## HTTP Methods (CRUD Operations)

REST APIs use standard HTTP methods to perform operations:

| HTTP Method | Operation | Purpose              | Example                 |
| ----------- | --------- | -------------------- | ----------------------- |
| GET         | Read      | Retrieve data        | Get list of books       |
| POST        | Create    | Add new data         | Add a new book          |
| PUT         | Update    | Modify existing data | Update a book's details |
| DELETE      | Delete    | Remove data          | Delete a book           |

### GET - Retrieve Data

```
GET /books           → Get all books
GET /books/1         → Get book with ID 1
```

**Characteristics:**
- Should not modify data
- Can be cached
- Safe to call multiple times (idempotent)

### POST - Create New Resource

```
POST /books
Body: { "title": "Python Guide" }
```

**Characteristics:**
- Creates a new resource
- Not idempotent (calling twice creates two resources)
- Usually returns the created resource

### PUT - Update Existing Resource

```
PUT /books/1
Body: { "title": "Updated Python Guide" }
```

**Characteristics:**
- Updates an existing resource
- Idempotent (same result if called multiple times)
- Requires complete resource data

### DELETE - Remove Resource

```
DELETE /books/1      → Delete book with ID 1
```

**Characteristics:**
- Removes a resource
- Idempotent (deleting twice has same effect as deleting once)


### Books API Overview
A simple book library API that stores data in a Python list. Data is lost when the server restarts.

**Features:**
- Add books
- Get all books
- Get book by index
- Update book 
- Delete books

### Running the API

```bash
uvicorn books:app --reload
```

Visit: `http://127.0.0.1:8000/docs`

## Testing Your APIs

### Using Swagger UI

1. Start your server
2. Visit `http://127.0.0.1:8000/docs`
3. Click on any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"
7. View response


## URL Structure

REST APIs use URLs to identify resources:

```
https://api.example.com/v1/books/123
│                      │  │     │
│                      │  │     └─ Resource ID
│                      │  └─────── Resource collection
│                      └────────── API version
└─────────────────────────────── Base URL
```

### Best Practices for URLs

- Use nouns, not verbs: `/books` not `/getBooks`
- Use plural names: `/books` not `/book`
- Use hierarchy for relationships: `/authors/5/books`
- Keep it simple and intuitive

## HTTP Status Codes

Status codes tell the client what happened with their request:

### Success Codes (2xx)
- **200 OK**: Request succeeded
- **201 Created**: New resource created successfully
- **204 No Content**: Request succeeded but no data to return

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Resource doesn't exist

### Server Error Codes (5xx)
- **500 Internal Server Error**: Something went wrong on the server

## Request and Response Format

### Request Components

1. **URL**: Where to send the request
2. **Method**: What operation to perform (GET, POST, etc.)
3. **Headers**: Metadata about the request
4. **Body**: Data being sent (for POST, PUT)

### Response Components

1. **Status Code**: Result of the request
2. **Headers**: Metadata about the response
3. **Body**: Data returned from the server

### Example Request/Response

**Request:**
```
POST /books HTTP/1.1
Content-Type: application/json

{
  "title": "Learning REST APIs",
  "author": "John Doe"
}
```

**Response:**
```
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 42,
  "title": "Learning REST APIs",
  "author": "John Doe",
  "created_at": "2024-01-09T10:30:00Z"
}
```

## JSON Data Format

JSON (JavaScript Object Notation) is the most common format for REST API data:

```json
{
  "id": 1,
  "title": "Python Basics",
  "author": "Jane Smith",
  "published": true,
  "pages": 250,
  "tags": ["python", "programming", "beginners"]
}
```

**Key Features:**
- Human-readable
- Easy to parse
- Supports objects, arrays, strings, numbers, booleans, null

## Practical Example: Books API

Let's design a simple books API:

### Endpoints

```
GET    /books           → List all books
GET    /books/{id}      → Get specific book
POST   /books           → Create new book
PUT    /books/{id}      → Update a book
DELETE /books/{id}      → Delete a book
```

### Sample Interactions

**Creating a Book:**
```
POST /books
Body: { "title": "REST API Guide" }

Response: 201 Created
{ "id": 1, "title": "REST API Guide" }
```

**Getting All Books:**
```
GET /books

Response: 200 OK
[
  { "id": 1, "title": "REST API Guide" },
  { "id": 2, "title": "Python Basics" }
]
```

**Updating a Book:**
```
PUT /books/1
Body: { "title": "Advanced REST APIs" }

Response: 200 OK
{ "id": 1, "title": "Advanced REST APIs" }
```

**Deleting a Book:**
```
DELETE /books/1

Response: 200 OK
{ "message": "Book deleted" }
```

## Testing REST APIs

### Tools for Testing

1. **Browser**: Good for simple GET requests
2. **Postman**: GUI tool for API testing
3. **cURL**: Command-line tool
4. **Python requests library**: Programmatic testing

### cURL Examples

```bash
# GET request
curl http://localhost:8000/books

# POST request
curl -X POST http://localhost:8000/books?title=MyBook

# DELETE request
curl -X DELETE http://localhost:8000/books/0
```

## Why Use REST APIs?

1. **Separation of Concerns**: Frontend and backend can be developed independently
2. **Scalability**: Easy to scale different parts of the application
3. **Flexibility**: Multiple clients (web, mobile, desktop) can use the same API
4. **Language Agnostic**: Client and server can be written in different languages
5. **Easy to Understand**: Uses familiar HTTP methods and status codes

## Common Patterns

### Filtering and Searching
```
GET /books?author=Smith&year=2023
```

### Pagination
```
GET /books?page=2&limit=10
```

### Sorting
```
GET /books?sort=title&order=asc
```

## Best Practices

1. **Use consistent naming conventions**
2. **Version your API** (`/v1/books`, `/v2/books`)
3. **Use appropriate HTTP methods and status codes**
4. **Keep responses simple and consistent**
5. **Document your API**
6. **Handle errors gracefully**
7. **Use JSON for data exchange**
8. **Keep URLs intuitive and hierarchical**

## Summary

REST APIs provide a standardized way to build web services that:
- Use HTTP methods for CRUD operations
- Are stateless and scalable
- Use clear, resource-based URLs
- Return standard HTTP status codes
- Typically use JSON for data exchange

This foundation allows you to build modern, scalable backend systems that can serve multiple types of clients efficiently.