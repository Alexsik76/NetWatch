from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import Response
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio

from .database import engine, Base, get_db
from . import models, crud, schemas
from .manager import manager
from .monitoring import monitor_devices


monitoring_task: asyncio.Task | None = None


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

@app.post("/devices/", response_model=schemas.Device, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(device: schemas.DeviceCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new device.
    Prevents creation if a device with the same MAC address already exists.
    """
    db_device = await crud.get_device_by_mac(db, mac_address=device.mac_address)
    if db_device:
        raise HTTPException(status_code=400, detail="MAC address already registered")
    return await crud.create_device(db=db, device=device)


@app.get("/devices/", response_model=List[schemas.Device])
async def read_devices_endpoint(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of devices.
    """
    devices = await crud.get_devices(db, skip=skip, limit=limit)
    return devices


@app.post("/devices/{device_id}/workloads/", response_model=schemas.Workload, status_code=status.HTTP_201_CREATED)
async def create_workload_for_device_endpoint(
        device_id: int, workload: schemas.WorkloadCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new workload associated with a specific device by its ID.
    """
    # First, check if the device exists
    db_device = await crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    # If the device exists, create the workload for it
    return await crud.create_workload_for_device(db=db, workload=workload, device_id=device_id)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main WebSocket endpoint for clients."""
    global monitoring_task

    await manager.connect(websocket)

    if not monitoring_task or monitoring_task.done():
        monitoring_task = asyncio.create_task(monitor_devices())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if len(manager.active_connections) == 0 and monitoring_task:
            print("INFO:     Last client disconnected. Stopping monitoring task...")
            monitoring_task.cancel()
            monitoring_task = None