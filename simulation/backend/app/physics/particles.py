"""
Particle and AntiParticle dataclasses for the antimatter simulation.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field

from .constants import (
    ELECTRON_MASS,
    PROTON_MASS,
    E_CHARGE,
    ELECTRON_MASS_MEV,
    PROTON_MASS_MEV,
    C_SQUARED,
    MEV_TO_JOULES,
)


@dataclass
class Particle:
    """A matter particle in 2-D simulation space."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    charge: float = -E_CHARGE       # electrons by default
    mass: float = ELECTRON_MASS     # kg
    spin: float = 0.5               # dimensionless (ℏ units)
    is_antimatter: bool = False
    energy: float = 0.0             # kinetic energy, Joules

    def __post_init__(self) -> None:
        if self.energy == 0.0:
            self.energy = self._kinetic_energy()

    def _kinetic_energy(self) -> float:
        v2 = self.vx ** 2 + self.vy ** 2
        return 0.5 * self.mass * v2

    def rest_energy_mev(self) -> float:
        return (self.mass * C_SQUARED) / MEV_TO_JOULES

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "charge": self.charge,
            "mass": self.mass,
            "spin": self.spin,
            "is_antimatter": self.is_antimatter,
            "energy": self.energy,
        }

    @classmethod
    def electron(cls, x: float = 0.0, y: float = 0.0,
                 vx: float = 0.0, vy: float = 0.0) -> "Particle":
        return cls(x=x, y=y, vx=vx, vy=vy,
                   charge=-E_CHARGE, mass=ELECTRON_MASS,
                   spin=0.5, is_antimatter=False)

    @classmethod
    def proton(cls, x: float = 0.0, y: float = 0.0,
               vx: float = 0.0, vy: float = 0.0) -> "Particle":
        return cls(x=x, y=y, vx=vx, vy=vy,
                   charge=+E_CHARGE, mass=PROTON_MASS,
                   spin=0.5, is_antimatter=False)


@dataclass
class AntiParticle(Particle):
    """An antimatter particle — same mass, opposite charge, is_antimatter=True."""

    charge: float = +E_CHARGE       # positrons by default (opposite to electron)
    mass: float = ELECTRON_MASS
    spin: float = 0.5
    is_antimatter: bool = True

    @classmethod
    def positron(cls, x: float = 0.0, y: float = 0.0,
                 vx: float = 0.0, vy: float = 0.0) -> "AntiParticle":
        return cls(x=x, y=y, vx=vx, vy=vy,
                   charge=+E_CHARGE, mass=ELECTRON_MASS,
                   spin=0.5, is_antimatter=True)

    @classmethod
    def antiproton(cls, x: float = 0.0, y: float = 0.0,
                   vx: float = 0.0, vy: float = 0.0) -> "AntiParticle":
        return cls(x=x, y=y, vx=vx, vy=vy,
                   charge=-E_CHARGE, mass=PROTON_MASS,
                   spin=0.5, is_antimatter=True)