from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.classify import router as classify_router
from app.db import Base, engine
from app import models  # noqa: F401 - registers TicketRecord with Base.metadata

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ticket Routing API")

# Dev-only: allows the static frontend (served from a different origin/port,
# or opened directly as a file://) to call this API. Restrict this before
# deploying anywhere real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(classify_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
