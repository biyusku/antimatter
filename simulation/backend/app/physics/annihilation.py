"""
Annihilation detection and energy calculation for matter-antimatter pairs.

Physics:
  E = mc²  (total rest-mass energy, both particles)
  For e+e-: 2 × 0.511 MeV gamma rays, emitted back-to-back (180°)
  For p+p̄:  ~938 MeV × 2, mostly into pions, ~0.1% lost to neutrinos
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

from .constants import C_SQUARED, MEV_TO_JOULES, TNT_JOULES_PER_KILOTON

if TYPE_CHECKING:
    from .particles import Particle

# Speed of light (task-spec value, kept separate from NIST constant)
c: float = 3e8           # m/s
electron_mass: float = 9.109e-31   # kg
proton_mass: float = 1.673e-27     # kg


def _distance_sq(p1: "Particle", p2: "Particle") -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return dx * dx + dy * dy


def detect_annihilation(
    p1: "Particle",
    p2: "Particle",
    threshold_distance: float,
) -> bool:
    """
    Return True if p1 and p2 are a matter-antimatter pair within
    threshold_distance of each other.

    Annihilation requires:
      - one is matter, the other antimatter
      - they are within threshold_distance (simulation units)
    """
    if p1.is_antimatter == p2.is_antimatter:
        return False
    return _distance_sq(p1, p2) <= threshold_distance ** 2


def calculate_energy(mass: float) -> dict:
    """
    Calculate annihilation energy for a particle–antiparticle pair.

    E = 2 × mass × c²  (both the particle and its antiparticle contribute)

    Args:
        mass: rest mass of one particle in kilograms

    Returns:
        dict with energy_joules, energy_mev, energy_kilotons_tnt
    """
    energy_joules = 2.0 * mass * C_SQUARED          # total pair energy
    energy_mev = energy_joules / MEV_TO_JOULES
    energy_kilotons_tnt = energy_joules / TNT_JOULES_PER_KILOTON

    return {
        "mass_kg": mass,
        "energy_joules": energy_joules,
        "energy_mev": energy_mev,
        "energy_kilotons_tnt": energy_kilotons_tnt,
    }


def annihilation_products(p1: "Particle", p2: "Particle") -> dict:
    """
    Describe the photon products of an annihilation event.

    e+e-  → 2γ at 511 keV each, back-to-back
    p+p̄   → pions → photons (hadronic channel, ~0.1% neutrino loss)
    """
    from .constants import ELECTRON_MASS, ELECTRON_MASS_MEV, PROTON_MASS_MEV

    mass = p1.mass
    mid_x = (p1.x + p2.x) / 2
    mid_y = (p1.y + p2.y) / 2

    if math.isclose(mass, ELECTRON_MASS, rel_tol=1e-3):
        photon_energy_mev = ELECTRON_MASS_MEV  # 0.511 MeV
        return {
            "process": "e+e-→2γ",
            "position": [mid_x, mid_y],
            "photon_count": 2,
            "photon_energy_mev": photon_energy_mev,
            "total_energy_mev": 2 * photon_energy_mev,
        }
    else:
        total_mev = 2 * PROTON_MASS_MEV * 0.999   # ~0.1% to neutrinos
        return {
            "process": "p+p̄→πons→γ",
            "position": [mid_x, mid_y],
            "photon_count": 4,
            "photon_energy_mev": total_mev / 4,
            "total_energy_mev": total_mev,
        }