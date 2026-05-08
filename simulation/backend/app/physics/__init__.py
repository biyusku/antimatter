"""
Physics package for the antimatter simulation.

Public API:
    SimulationEngine  — stateful engine: step(), get_state(), reset(), set_scenario()
    Particle          — matter particle dataclass
    AntiParticle      — antimatter particle dataclass
    ElectromagneticField — Lorentz force field
    detect_annihilation  — pair proximity check
    calculate_energy     — E = mc² for a particle-antiparticle pair
"""

from .simulation_engine import SimulationEngine
from .particles import Particle, AntiParticle
from .fields import ElectromagneticField
from .annihilation import detect_annihilation, calculate_energy, produce_photons

__all__ = [
    "SimulationEngine",
    "Particle",
    "AntiParticle",
    "ElectromagneticField",
    "detect_annihilation",
    "calculate_energy",
    "produce_photons",
]