from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Minimal FastAPI server works"}


@app.get("/health")
async def health():
    return {"status": "healthy"}