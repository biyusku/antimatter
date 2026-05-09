"""
SimulationEngine — high-level driver used by the WebSocket API.

Manages a population of Particle / AntiParticle objects, steps them through
the EM field, detects annihilations, and returns JSON-serialisable state.
"""

from __future__ import annotations
import math
import random
import time
from typing import Any

from .particles import Particle, AntiParticle
from .annihilation import detect_annihilation, calculate_energy, produce_photons
from .fields import ElectromagneticField
from .constants import ELECTRON_MASS, PROTON_MASS, E_CHARGE

# Speed of light and masses per task spec
c: float = 3e8
electron_mass: float = 9.109e-31
proton_mass: float = 1.673e-27

_SCENARIO_DEFAULTS: dict[str, dict] = {
    "default": {
        "n_matter": 20,
        "n_antimatter": 20,
        "speed_scale": 1e6,
        "mass": electron_mass,
        "charge": E_CHARGE,
        "annihilation_threshold": 0.3,
        "field": {"Bz": 0.0, "Ex": 0.0, "Ey": 0.0},
    },
    "electron_positron": {
        "n_matter": 30,
        "n_antimatter": 30,
        "speed_scale": 2e6,
        "mass": electron_mass,
        "charge": E_CHARGE,
        "annihilation_threshold": 0.25,
        "field": {"Bz": 1e-3, "Ex": 0.0, "Ey": 0.0},
    },
    "proton_antiproton": {
        "n_matter": 15,
        "n_antimatter": 15,
        "speed_scale": 5e5,
        "mass": proton_mass,
        "charge": E_CHARGE,
        "annihilation_threshold": 0.2,
        "field": {"Bz": 0.5, "Ex": 0.0, "Ey": 0.0},
    },
    "mixed": {
        "n_matter": 25,
        "n_antimatter": 25,
        "speed_scale": 1.5e6,
        "mass": electron_mass,
        "charge": E_CHARGE,
        "annihilation_threshold": 0.3,
        "field": {"Bz": 2e-4, "Ex": 1e3, "Ey": 0.0},
    },
}

_BOUNDS = 10.0   # simulation box half-size (arbitrary units)


def _rand_particle(mass: float, charge: float, speed_scale: float) -> Particle:
    x = random.uniform(-_BOUNDS, _BOUNDS)
    y = random.uniform(-_BOUNDS, _BOUNDS)
    speed = random.gauss(speed_scale, speed_scale * 0.2)
    angle = random.uniform(0, 2 * math.pi)
    vx = speed * math.cos(angle)
    vy = speed * math.sin(angle)
    return Particle(x=x, y=y, vx=vx, vy=vy,
                    charge=-charge, mass=mass, spin=0.5, is_antimatter=False)


def _rand_antiparticle(mass: float, charge: float, speed_scale: float) -> AntiParticle:
    x = random.uniform(-_BOUNDS, _BOUNDS)
    y = random.uniform(-_BOUNDS, _BOUNDS)
    speed = random.gauss(speed_scale, speed_scale * 0.2)
    angle = random.uniform(0, 2 * math.pi)
    vx = speed * math.cos(angle)
    vy = speed * math.sin(angle)
    return AntiParticle(x=x, y=y, vx=vx, vy=vy,
                        charge=+charge, mass=mass, spin=0.5, is_antimatter=True)


class SimulationEngine:
    """
    Stateful particle simulation engine.

    Usage:
        engine = SimulationEngine(scenario='electron_positron')
        state = engine.get_state()      # initial snapshot
        for _ in range(100):
            state = engine.step(dt=1e-9)
        engine.reset()
    """

    def __init__(self, scenario: str = "default") -> None:
        self._scenario: str = scenario
        self._particles: list[Particle | AntiParticle] = []
        self._field: ElectromagneticField = ElectromagneticField()
        self._annihilation_count: int = 0
        self._total_energy_joules: float = 0.0
        self._step_count: int = 0
        self._total_photons: int = 0
        self._init_scenario(scenario)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_particle(self, particle: Particle | AntiParticle) -> None:
        """Append an externally constructed particle to the simulation."""
        self._particles.append(particle)

    def step(self, dt: float = 1e-9) -> dict:
        """
        Advance the simulation by one time step of length dt (seconds).

        Applies Lorentz forces, integrates positions, detects and removes
        annihilating pairs, and returns the new state.
        """
        self._step_count += 1
        annihilation_events: list[dict] = []

        # Apply field forces + integrate (skip dead particles handled below)
        for p in self._particles:
            self._field.apply(p, dt)
            # Elastic reflection at box walls
            if abs(p.x) >= _BOUNDS:
                p.vx = -p.vx
                p.x = math.copysign(_BOUNDS, p.x)
            if abs(p.y) >= _BOUNDS:
                p.vy = -p.vy
                p.y = math.copysign(_BOUNDS, p.y)

        # Annihilation detection — O(n×m), fine for n < 200
        matter = [p for p in self._particles if not p.is_antimatter]
        antimatter = [p for p in self._particles if p.is_antimatter]
        dead_m: set[str] = set()
        dead_a: set[str] = set()

        for mp in matter:
            if mp.id in dead_m:
                continue
            for ap in antimatter:
                if ap.id in dead_a:
                    continue
                if detect_annihilation(mp, ap, dt=dt, threshold=self._threshold):
                    dead_m.add(mp.id)
                    dead_a.add(ap.id)
                    products = produce_photons(mp, ap)
                    energy = calculate_energy(mp.mass)
                    self._annihilation_count += 1
                    self._total_energy_joules += energy["energy_joules"]
                    self._total_photons += products["photon_count"]
                    annihilation_events.append({**products, **energy})
                    break

        if dead_m or dead_a:
            self._particles = [
                p for p in self._particles
                if p.id not in dead_m and p.id not in dead_a
            ]

        return self.get_state(annihilation_events=annihilation_events)

    def get_state(self, annihilation_events: list[dict] | None = None) -> dict:
        """
        Return a JSON-serialisable snapshot of the current simulation state.

        Keys:
            particles   — list of particle dicts
            stats       — annihilation_count, total_energy, particle_count
            timestamp   — float (Unix time)
            step        — current step number
            events      — annihilation events from the most recent step
        """
        return {
            "particles": [p.to_dict() for p in self._particles],
            "stats": {
                "annihilation_count": self._annihilation_count,
                "total_energy": self._total_energy_joules,
                "particle_count": len(self._particles),
                "matter_count": sum(1 for p in self._particles if not p.is_antimatter),
                "antimatter_count": sum(1 for p in self._particles if p.is_antimatter),
                "photon_count": self._total_photons,
                "step": self._step_count,
            },
            "timestamp": time.time(),
            "step": self._step_count,
            "scenario": self._scenario,
            "events": annihilation_events or [],
        }

    def reset(self) -> None:
        """Reset simulation to initial conditions for the current scenario."""
        self._annihilation_count = 0
        self._total_energy_joules = 0.0
        self._total_photons = 0
        self._step_count = 0
        self._particles = []
        self._init_scenario(self._scenario)

    def set_scenario(self, name: str) -> None:
        """Switch to a named scenario and reinitialise."""
        self._scenario = name
        self.reset()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_scenario(self, name: str) -> None:
        cfg = _SCENARIO_DEFAULTS.get(name, _SCENARIO_DEFAULTS["default"])
        self._threshold = cfg["annihilation_threshold"]
        f = cfg["field"]
        self._field = ElectromagneticField(Bz=f["Bz"], Ex=f["Ex"], Ey=f["Ey"])
        self._particles = []
        for _ in range(cfg["n_matter"]):
            self._particles.append(
                _rand_particle(cfg["mass"], cfg["charge"], cfg["speed_scale"])
            )
        for _ in range(cfg["n_antimatter"]):
            self._particles.append(
                _rand_antiparticle(cfg["mass"], cfg["charge"], cfg["speed_scale"])
            )