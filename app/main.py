from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="ROMANTIK AI API",
    description=(
        "API untuk pemeriksaan formulir ROMANTIK "
        "menggunakan Hybrid AI berbasis Rule-Based System "
        "dan Fine-Tuned LLM."
    ),
    version="0.1.0",
)


app.include_router(router)


@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {
        "message": "ROMANTIK AI API is running"
    }