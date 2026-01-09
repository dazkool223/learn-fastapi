## Counter API

### Purpose

The Counter API demonstrates how to maintain and modify state in a backend application. It's a simple example of how APIs can store and manipulate data across multiple requests.

### Endpoints

| Method | Endpoint     | Description            | Returns               |
| ------ | ------------ | ---------------------- | --------------------- |
| POST   | `/increment` | Increases counter by 1 | Current counter value |
| POST   | `/decrement` | Decreases counter by 1 | Current counter value |
| GET    | `/counter`   | Gets current value     | Current counter value |

### Code Structure

```python
from fastapi import FastAPI

app = FastAPI()

counter = 0  # Global variable to store state

@app.post("/increment")
def increment():
    global counter
    counter += 1
    return {"counter": counter}

@app.post("/decrement")
def decrement():
    global counter
    counter -= 1
    return {"counter": counter}

@app.get("/counter")
def get_counter():
    return {"counter": counter}
```

### Key Concepts

**Global State**: The `counter` variable is stored in memory at the module level, making it accessible across all requests. The `global` keyword is needed to modify it from within functions.

**State Persistence**: The counter value persists across requests but only during the application's runtime. If you restart the server, the counter resets to 0.

**HTTP Method Choice**: We use POST for increment/decrement because these operations modify state. GET is used to retrieve the value without changing it.

### Usage Examples

**Starting the server:**
```bash
uvicorn counter_api:app --reload
```

**Testing with cURL:**
```bash
# Increment the counter
curl -X POST http://localhost:8000/increment
# Response: {"counter": 1}

# Increment again
curl -X POST http://localhost:8000/increment
# Response: {"counter": 2}

# Decrement
curl -X POST http://localhost:8000/decrement
# Response: {"counter": 1}

# Check current value
curl http://localhost:8000/counter
# Response: {"counter": 1}
```

### Real-World Applications

This pattern is useful for:
- View counters for blog posts or videos
- Like/dislike counters
- Inventory management (stock quantities)
- Rate limiting counters
- Session counters

### Limitations

**Not Production-Ready**: This implementation has limitations:
- Data is lost when the server restarts
- Not thread-safe for concurrent requests
- Single instance only (won't work with multiple servers)

**Production Solutions**: Use databases (Redis, PostgreSQL) or atomic operations for real applications.
