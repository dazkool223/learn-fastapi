from fastapi import FastAPI

app = FastAPI()

counter = 0

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