from fastapi import FastAPI

from app.api.routes.classify import router as classify_router

app = FastAPI(title="Ticket Routing API")

app.include_router(classify_router)


@app.get("/health")
def health():
    return {"status": "ok"}
