from fastapi import FastAPI
from fastapi import status
from fastapi.responses import Response
from contextlib import asynccontextmanager

from .database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
       Provides a handler for the browser's request for a favicon.
       Returns a 204 No Content response to prevent 404 errors in the logs.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@app.get("/")
async def read_root():
    """
    A simple root endpoint to check if the API is running.
    """
    return {"message": "Welcome to NetWatch API"}