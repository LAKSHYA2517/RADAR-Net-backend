from fastapi import FastAPI
from app.api.routes import router  # Use full path instead of just 'routes'

app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "RADAR-Net Backend API"}