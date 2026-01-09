## Path Parameters & Query Parameters

### Path Parameters

```python
from fastapi import FastAPI

app = FastAPI()

# Path parameter
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

# Multiple path parameters
@app.get("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id}

# Path parameter with type validation
@app.get("/items/{item_id}")
def get_item(item_id: int):
    # FastAPI automatically validates that item_id is an integer
    return {"item_id": item_id, "type": type(item_id).__name__}
```

### Query Parameters

```python
from fastapi import FastAPI

app = FastAPI()

# Query parameters
# URL: /search?q=python&limit=10
@app.get("/search")
def search(q: str, limit: int = 10):
    return {"query": q, "limit": limit}

# Optional query parameters
@app.get("/items")
def get_items(skip: int = 0, limit: int = 10, sort: str = None):
    return {
        "skip": skip,
        "limit": limit,
        "sort": sort
    }

# Boolean query parameters
# URL: /filter?active=true
@app.get("/filter")
def filter_items(active: bool = True):
    return {"active": active}
```

### Combining Path and Query Parameters

```python
@app.get("/users/{user_id}/items")
def get_user_items(user_id: int, skip: int = 0, limit: int = 10):
    return {
        "user_id": user_id,
        "skip": skip,
        "limit": limit,
        "items": []
    }
```
---

## Authentication & Authorization

**Authentication** verifies who you are, **Authorization** determines what you can access.

**JWT (JSON Web Tokens)**: Stateless authentication tokens containing encoded user information. The server signs the token, and clients include it in request headers.

**OAuth 2.0**: Industry-standard protocol for authorization, commonly used for "Login with Google/Facebook" functionality.

**Session-based Auth**: Server stores session data, sends session ID to client via cookies. More secure but requires server-side storage.

## Middleware

Middleware functions execute between receiving a request and sending a response. Common uses include logging, authentication checks, request validation, and error handling.

```python
# Example: Logging middleware
def log_requests(request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = call_next(request)
    return response
```

## Database Integration

**ORM (Object-Relational Mapping)**: Libraries like SQLAlchemy or Django ORM let you interact with databases using Python objects instead of raw SQL.

**Connection Pooling**: Reusing database connections instead of creating new ones for each request improves performance.

**Migrations**: Version control for database schemas, allowing you to track and apply schema changes systematically.

## API Design Patterns

**Pagination**: Break large datasets into pages to improve performance and user experience.

```python
GET /books?page=2&limit=20
```

**Filtering & Sorting**: Allow clients to query specific data.

```python
GET /books?author=Smith&sort=title&order=desc
```

**Rate Limiting**: Prevent API abuse by limiting requests per user/IP within a time window.

**Versioning**: Use `/v1/`, `/v2/` in URLs or headers to maintain backward compatibility while evolving your API.

## Asynchronous Programming

**Async/Await**: Handle I/O operations without blocking, enabling higher concurrency.

```python
async def get_user(user_id):
    user = await database.fetch_user(user_id)
    return user
```

**Background Tasks**: Offload time-consuming operations like sending emails or processing images to background workers.

**WebSockets**: Enable real-time, bidirectional communication between client and server for chat apps, live updates, or gaming.

## Caching Strategies

**In-Memory Cache**: Store frequently accessed data in RAM (Redis, Memcached) for instant retrieval.

**HTTP Caching**: Use cache headers to let browsers/CDNs cache responses.

**Database Query Caching**: Cache expensive database query results.

## Error Handling & Logging

**Structured Logging**: Use JSON logs with consistent fields for easier parsing and analysis.

**Error Middleware**: Centralized error handling that catches exceptions and returns appropriate responses.

**Custom Exceptions**: Define domain-specific exceptions for better error management.

## Security Best Practices

**Input Validation**: Always validate and sanitize user input to prevent injection attacks.

**CORS (Cross-Origin Resource Sharing)**: Control which domains can access your API.

**HTTPS**: Encrypt data in transit using SSL/TLS certificates.

**Environment Variables**: Store secrets and configuration outside your codebase.

**SQL Injection Prevention**: Use parameterized queries or ORMs instead of string concatenation.

## Testing

**Unit Tests**: Test individual functions in isolation.

**Integration Tests**: Test how multiple components work together.

**API Testing**: Test endpoints with various inputs and verify responses.

**Mocking**: Simulate external dependencies (databases, APIs) during testing.

## Performance Optimization

**Database Indexing**: Speed up queries by indexing frequently searched columns.

**Query Optimization**: Use select specific fields, avoid N+1 queries, use joins efficiently.

**Lazy Loading**: Load data only when needed rather than all at once.

**Compression**: Gzip responses to reduce bandwidth usage.

**Load Balancing**: Distribute traffic across multiple servers.

## API Documentation

**OpenAPI/Swagger**: Auto-generate interactive API documentation from your code.

**Postman Collections**: Share API endpoint collections with your team.

## CORS and Security Headers

Set appropriate headers to control browser security policies and enable cross-origin requests where needed while protecting against common vulnerabilities.

## Dependency Injection

Pattern where dependencies are provided to a component rather than created inside it, improving testability and maintainability.

## Environment Configuration

Separate configuration for development, staging, and production environments using environment variables and config files.

---

These techniques form the foundation of professional backend development, enabling you to build secure, scalable, and maintainable web applications.