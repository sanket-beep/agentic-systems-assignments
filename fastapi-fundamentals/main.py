from fastapi import FastAPI
import json

app = FastAPI()

@app.get("/search")
def search(name: str, age: int):
    response_dict = {
        'name' : name,
        'age' : age
    }
    return json.dumps(response_dict)