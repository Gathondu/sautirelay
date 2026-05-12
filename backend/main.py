import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
async def status():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
