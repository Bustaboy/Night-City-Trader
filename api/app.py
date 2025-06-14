from fastapi import FastAPI
from config.settings import settings

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Local trading bot API"}
