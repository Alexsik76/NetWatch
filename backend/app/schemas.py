from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

from .models import WorkloadType


# --- Workload Schemas ---

class WorkloadBase(BaseModel):
    """Base schema for a workload with fields common to creation and reading."""
    name: str
    workload_type: WorkloadType
    port: Optional[int] = None
    definition: Optional[str] = None
    run_as_user: Optional[str] = None
    run_as_group: Optional[str] = None
    image: Optional[str] = None
    container_id: Optional[str] = None


class WorkloadCreate(WorkloadBase):
    """Schema used for creating a new workload. Requires a device_id."""
    pass


class Workload(WorkloadBase):
    """Schema for reading a workload from the API. Includes DB-generated fields."""
    id: int
    status: str
    device_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Device Schemas ---

class DeviceBase(BaseModel):
    """Base schema for a device with fields common to creation and reading."""
    mac_address: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    is_disabled: Optional[bool] = False


class DeviceCreate(DeviceBase):
    """Schema used for creating a new device."""
    pass


class Device(DeviceBase):
    """
    Schema for reading a device from the API.
    Includes DB-generated fields and a list of associated workloads.
    """
    id: int
    is_online: bool
    last_seen: Optional[datetime] = None
    first_seen: datetime
    last_status_change: Optional[datetime] = None

    # This will hold the list of related Workload objects
    workloads: List[Workload] = []

    # This config allows Pydantic to read data from ORM model attributes
    model_config = ConfigDict(from_attributes=True)