"""
Electromagnetic field model for the antimatter simulation.

Uses the relativistic Boris push integrator:
    - Exact energy conservation for magnetic rotation at all speeds.
    - Correct relativistic velocity v = p/(γm).

For a 2-D simulation B is treated as a scalar out-of-plane component (Bz),
and E is a 2-D vector (Ex, Ey). The Boris push is performed in 3-D (pz=0)
and the z-components are discarded afterward.
"""

from __future__ import annotations
import math
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

        Uses the Boris push — a relativistic, symplectic integrator that
        conserves energy exactly for the magnetic rotation step:

          1. Half electric kick:   p⁻ = p + (q/2) E dt
          2. Magnetic rotation:    p⁺ = rotate(p⁻, t)  where t = qB dt/(2γm)
          3. Half electric kick:   p_new = p⁺ + (q/2) E dt
          4. Update position:      x += (p_new / γm) dt

        Works at all speeds; reduces to the classical leapfrog at v ≪ c.
        """
        C_LIGHT: float = 2.99792458e8   # m/s

        q = particle.charge
        m = particle.mass

        # Current momentum p = γmv
        vx, vy = particle.vx, particle.vy
        v2 = vx * vx + vy * vy
        gamma = 1.0 / math.sqrt(max(1.0 - v2 / (C_LIGHT * C_LIGHT), 1.0e-10))
        px = gamma * m * vx
        py = gamma * m * vy

        # 1. Half electric kick
        half_qEdt = 0.5 * q * dt
        px_minus = px + half_qEdt * self.Ex
        py_minus = py + half_qEdt * self.Ey

        # 2. Magnetic rotation (Boris) — B along z only, so t = (0, 0, tz)
        p_minus_sq = px_minus * px_minus + py_minus * py_minus
        gamma_minus = math.sqrt(1.0 + p_minus_sq / (m * m * C_LIGHT * C_LIGHT))
        tz = (q * self.Bz * dt) / (2.0 * gamma_minus * m)
        sz = 2.0 * tz / (1.0 + tz * tz)
        # p' = p⁻ + p⁻ × t   (cross with t=(0,0,tz): px'=px+py*tz, py'=py-px*tz)
        px_prime = px_minus + py_minus * tz
        py_prime = py_minus - px_minus * tz
        # p⁺ = p⁻ + p' × s
        px_plus = px_minus + py_prime * sz
        py_plus = py_minus - px_prime * sz

        # 3. Second half electric kick
        px_new = px_plus + half_qEdt * self.Ex
        py_new = py_plus + half_qEdt * self.Ey

        # 4. Recover velocity and update position
        p_new_sq = px_new * px_new + py_new * py_new
        gamma_new = math.sqrt(1.0 + p_new_sq / (m * m * C_LIGHT * C_LIGHT))
        particle.vx = px_new / (gamma_new * m)
        particle.vy = py_new / (gamma_new * m)
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt

    def to_dict(self) -> dict:
        return {"Bz": self.Bz, "Ex": self.Ex, "Ey": self.Ey}