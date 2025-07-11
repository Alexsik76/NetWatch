from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas


async def get_device_by_mac(db: AsyncSession, mac_address: str) -> models.Device | None:
    """
    Retrieve a device from the database by its MAC address.
    """
    query = select(models.Device).options(selectinload(models.Device.workloads)).where(
        models.Device.mac_address == mac_address)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_devices(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[models.Device]:
    """
    Retrieve a list of devices from the database with pagination.
    """
    query = select(models.Device).options(selectinload(models.Device.workloads)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_device(db: AsyncSession, device: schemas.DeviceCreate) -> models.Device:
    """
    Create a new device in the database.
    """
    # Convert the Pydantic schema to a dictionary
    device_data = device.model_dump()

    # Create a SQLAlchemy model instance
    db_device = models.Device(**device_data)

    # Add the instance to the session and commit
    db.add(db_device)
    await db.commit()

    # Refresh the instance to get the data generated by the database (like id, first_seen)
    await db.refresh(db_device)

    return db_device

async def get_device(db: AsyncSession, device_id: int) -> models.Device | None:
    """
    Retrieve a single device by its ID.
    Eagerly loads associated workloads.
    """
    query = select(models.Device).options(selectinload(models.Device.workloads)).where(models.Device.id == device_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_workload_for_device(db: AsyncSession, workload: schemas.WorkloadCreate, device_id: int) -> models.Workload:
    """
    Create a new workload for a specific device.
    """
    workload_data = workload.model_dump()
    db_workload = models.Workload(**workload_data, device_id=device_id)
    db.add(db_workload)
    await db.commit()
    await db.refresh(db_workload)
    return db_workload