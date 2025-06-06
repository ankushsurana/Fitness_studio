from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Sample data
fake_classes_db = [
    {"id": 1, "name": "Math 101", "teacher": "Mr. Smith"},
    {"id": 2, "name": "Science 101", "teacher": "Mrs. Johnson"},
]

class Class(BaseModel):
    id: int
    name: str
    teacher: str

@app.get("/api/classes", response_model=List[Class])
async def get_classes():
    return fake_classes_db

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_classes():
    response = client.get("/api/classes")
    assert response.status_code == 200
    assert "classes" in response.json()
