from fastapi import FastAPI
from app.api.routes import router  # Use full path instead of just 'routes'
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(router)

origins = [
    "http://localhost:3000",  # Default React (Create React App)
    "http://localhost:5173",  # Default Vite
    "http://127.0.0.1:5173",  # Alternative Vite address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Allows specific list of origins
    allow_credentials=True,            # Allows cookies/auth headers
    allow_methods=["*"],               # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],               # Allows all headers (Content-Type, etc.)
)

@app.get("/")
def read_root():
    return {"message": "RADAR-Net Backend API"}