from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# This defines what data your Node server will send you
class Payload(BaseModel):
    text: str
    # You can add more fields later when the theme drops

@app.get("/")
def health_check():
    return {"status": "Brain is online"}

@app.post("/process")
def process_data(payload: Payload):
    # ---------------------------------------------------------
    # HACKATHON LOGIC GOES HERE LATER
    # Right now, we just fake the processing
    print(f"Received from Node: {payload.text}")
    
    fake_result = f"Python processed: {payload.text.upper()}"
    # ---------------------------------------------------------
    
    return {"status": "success", "output": fake_result} 