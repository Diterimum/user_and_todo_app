from fastapi import FastAPI

from db import init_db
from controllers.auth import router as auth_router
from controllers.todos import router as todos_router

app = FastAPI(title="Todo API (ORM, no IDs)")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root():
    return {"ok": True, "service": "Todo API"}


app.include_router(auth_router)
app.include_router(todos_router)