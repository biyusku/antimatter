import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    github_id = Column(Integer, unique=True, index=True)
    github_username = Column(String, unique=True, index=True)
    github_avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    simulations = relationship("Simulation", back_populates="user")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=True)
    simulation_type = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    results = Column(JSON, nullable=True)
    total_energy_mev = Column(Float, nullable=True)
    energy_kilotons_tnt = Column(Float, nullable=True)
    total_annihilations = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    is_public = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="simulations")