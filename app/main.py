from fastapi import FastAPI

app = FastAPI(title="My Backend API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/version")
def version_check():
    return {"version": "0.1.0"}