import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class WorkloadType(enum.Enum):
    """Defines the types of workloads we can monitor."""
    CONTAINER_DOCKER = "docker_container"
    CONTAINER_PODMAN = "podman_container"
    CONTAINER_LXC = "lxc_container"
    SYSTEMD_UNIT = "systemd_unit"
    VIRTUAL_MACHINE = "virtual_machine"
    PROCESS = "process"


class Device(Base):
    """SQLAlchemy model for a network device."""
    __tablename__ = "devices"

    id: int = Column(Integer, primary_key=True, index=True)
    mac_address: str = Column(String, unique=True, index=True, nullable=False)
    ip_address: str = Column(String, index=True, nullable=True)
    hostname: str = Column(String, index=True, nullable=True)
    name: str = Column(String, nullable=True)
    notes: str = Column(String, nullable=True)
    is_disabled: bool = Column(Boolean, default=False, nullable=False, index=True)
    disabled_at: datetime.datetime = Column(DateTime(timezone=True), nullable=True)
    is_online: bool = Column(Boolean, default=False, nullable=False)
    last_seen: datetime.datetime = Column(DateTime(timezone=True), nullable=True)
    first_seen: datetime.datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_status_change: datetime.datetime = Column(DateTime(timezone=True), nullable=True)

    workloads = relationship("Workload", back_populates="device", cascade="all, delete-orphan")


class Workload(Base):
    """
    SQLAlchemy model for a workload running on a device.
    This can be a container, a systemd unit, a VM, etc.
    """
    __tablename__ = "workloads"

    id: int = Column(Integer, primary_key=True, index=True)

    # --- Core Information ---
    name: str = Column(String, nullable=False, index=True)  # e.g., "nginx-proxy" or "postgresql.service"
    workload_type: WorkloadType = Column(Enum(WorkloadType), nullable=False)
    status: str = Column(String, default="unknown", nullable=False) # e.g., "running", "stopped", "degraded"
    port: int = Column(Integer, nullable=True) # Port for active health checks

    # --- Definition and Execution Context ---
    definition: str = Column(Text, nullable=True)  # For docker-compose, systemd unit file content, run command
    run_as_user: str = Column(String, nullable=True)
    run_as_group: str = Column(String, nullable=True)

    # --- Container-Specific Fields (nullable) ---
    image: str = Column(String, nullable=True) # e.g., "nginx:latest"
    container_id: str = Column(String, nullable=True, index=True)

    # --- Relationship ---
    device_id: int = Column(Integer, ForeignKey("devices.id"), nullable=False)
    device = relationship("Device", back_populates="workloads")