"""
Electromagnetic field model for the antimatter simulation.

Uses the non-relativistic Lorentz force law:
    F = q(E + v × B)

For a 2-D simulation B is treated as a scalar out-of-plane component (Bz),
and E is a 2-D vector (Ex, Ey).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .particles import Particle


@dataclass
class ElectromagneticField:
    """
    Uniform or configurable EM field that exerts Lorentz force on particles.

    Attributes:
        Bz: out-of-plane magnetic field component (Tesla)
        Ex: x-component of electric field (V/m)
        Ey: y-component of electric field (V/m)
    """

    Bz: float = 0.0    # Tesla
    Ex: float = 0.0    # V/m
    Ey: float = 0.0    # V/m

    def lorentz_force(
        self,
        particle: "Particle",
        B_field: float | None = None,
        E_field: tuple[float, float] | None = None,
    ) -> tuple[float, float]:
        """
        Compute the 2-D Lorentz force on a particle.

            F = q(E + v × B)

        In 2-D, v × B_z gives an in-plane force:
            (v × B)_x =  vy * Bz
            (v × B)_y = -vx * Bz

        Args:
            particle:  the Particle or AntiParticle instance
            B_field:   override for Bz (Tesla); uses self.Bz if None
            E_field:   override for (Ex, Ey) (V/m); uses self.Ex/Ey if None

        Returns:
            (Fx, Fy) force in Newtons
        """
        q = particle.charge
        vx = particle.vx
        vy = particle.vy

        Bz = B_field if B_field is not None else self.Bz
        Ex = E_field[0] if E_field is not None else self.Ex
        Ey = E_field[1] if E_field is not None else self.Ey

        # Electric force component
        fe_x = q * Ex
        fe_y = q * Ey

        # Magnetic force component (v × B in 2-D, B along z-axis)
        fm_x = q * vy * Bz
        fm_y = -q * vx * Bz

        return (fe_x + fm_x, fe_y + fm_y)

    def apply(self, particle: "Particle", dt: float) -> None:
        """
        Apply Lorentz force to particle in-place for time step dt.

        Uses Euler integration:  v += (F/m) * dt
        """
        Fx, Fy = self.lorentz_force(particle)
        ax = Fx / particle.mass
        ay = Fy / particle.mass
        particle.vx += ax * dt
        particle.vy += ay * dt
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt

    def to_dict(self) -> dict:
        return {"Bz": self.Bz, "Ex": self.Ex, "Ey": self.Ey}