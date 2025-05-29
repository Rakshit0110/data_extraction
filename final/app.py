from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from train import router as first_app
from extract import router as second_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(first_app, prefix="/first_app")
app.include_router(second_app, prefix="/second_app")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
