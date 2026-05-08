"""
Monte Carlo annihilation simulation engine + PhysicsEngine utility class.

SimulationRunner: batched Monte Carlo for WebSocket streaming.
PhysicsEngine: stateless calculations (annihilation energy, cross-sections).
"""

import math
from typing import Any

import numpy as np

from .constants import (
    ELECTRON_MASS_MEV,
    LITTLE_BOY_YIELD_KT,
    MEV_TO_JOULES,
    PROTON_MASS_MEV,
    R_E,
    TNT_JOULES_PER_KILOTON,
    TNT_JOULES_PER_MEGATON,
    TSAR_BOMBA_YIELD_MT,
    C_SQUARED,
)


# ---------------------------------------------------------------------------
# PhysicsEngine — stateless, reusable calculations
# ---------------------------------------------------------------------------

class PhysicsEngine:
    """Stateless physics calculation engine. Instantiated once as a singleton."""

    # --- Energy calculations -----------------------------------------------

    def annihilation_energy(
        self,
        matter_kg: float,
        antimatter_kg: float | None = None,
    ) -> dict:
        """
        Calculate energy released by complete matter-antimatter annihilation.

        Args:
            matter_kg: mass of matter in kilograms
            antimatter_kg: mass of antimatter in kilograms (defaults to matter_kg)

        Returns:
            dict with energy_joules, energy_kilotons_tnt, hiroshima_multiples,
            efficiency_percent, and supporting values.
        """
        if antimatter_kg is None:
            antimatter_kg = matter_kg

        total_mass_kg = matter_kg + antimatter_kg
        # ~99.9% efficiency: ~0.1% lost to neutrinos in p+p̄ channel
        energy_j = total_mass_kg * C_SQUARED * 0.999
        energy_kt = energy_j / TNT_JOULES_PER_KILOTON
        energy_mt = energy_j / TNT_JOULES_PER_MEGATON
        energy_mev = energy_j / MEV_TO_JOULES

        return {
            "matter_kg": matter_kg,
            "antimatter_kg": antimatter_kg,
            "total_mass_kg": total_mass_kg,
            "energy_joules": energy_j,
            "energy_mev": energy_mev,
            "energy_kilotons_tnt": energy_kt,
            "energy_megatons_tnt": energy_mt,
            "efficiency_percent": 99.9,
            "hiroshima_multiples": energy_kt / LITTLE_BOY_YIELD_KT,
            "tsar_bomba_fraction": energy_mt / TSAR_BOMBA_YIELD_MT,
        }

    # --- Cross-section calculations ----------------------------------------

    def klein_nishina_cross_section(self, energy_mev: float) -> float:
        """
        Klein-Nishina total cross-section for Compton scattering / e+e- annihilation.

        Uses the exact analytic formula (Heitler 1954):
            sigma = 2*pi*r_e^2 * { [(1+eps)/eps^2] * [2(1+eps)/(1+2eps) - ln(1+2eps)/eps]
                                   + ln(1+2eps)/(2eps) - (1+3eps)/(1+2eps)^2 }

        Args:
            energy_mev: photon / centre-of-mass energy in MeV

        Returns:
            Cross-section in cm^2
        """
        epsilon = energy_mev / ELECTRON_MASS_MEV

        if epsilon < 1e-6:
            # Thomson limit: sigma_T = (8/3) * pi * r_e^2
            return (8.0 / 3.0) * math.pi * R_E ** 2 * 1e4  # m^2 -> cm^2

        ln2e = math.log(1.0 + 2.0 * epsilon)
        term1 = (1.0 + epsilon) / epsilon ** 2 * (
            2.0 * (1.0 + epsilon) / (1.0 + 2.0 * epsilon) - ln2e / epsilon
        )
        term2 = ln2e / (2.0 * epsilon)
        term3 = (1.0 + 3.0 * epsilon) / (1.0 + 2.0 * epsilon) ** 2

        cs_m2 = 2.0 * math.pi * R_E ** 2 * (term1 + term2 - term3)
        return abs(cs_m2) * 1e4  # m^2 -> cm^2


# Singleton — import this everywhere instead of re-instantiating
physics_engine = PhysicsEngine()


# ---------------------------------------------------------------------------
# SimulationRunner — stateful Monte Carlo for WebSocket streaming
# ---------------------------------------------------------------------------

class SimulationRunner:
    def __init__(self, params: dict[str, Any]) -> None:
        self.sim_type = params.get("simulation_type", "electron_positron")
        self.particle_count = min(int(params.get("particle_count", 1000)), 50_000)
        self.total_steps = min(int(params.get("monte_carlo_steps", 10_000)), 500_000)
        self.beam_energy_mev = float(params.get("beam_energy_mev", 1.0))
        self.rng = np.random.default_rng()
        self.running = True
        self.step = 0
        self.collisions = 0
        self.annihilations = 0
        self.photons = 0
        self.total_energy_mev = 0.0
        self.events: list[dict] = []

    # ------------------------------------------------------------------
    # Single-event samplers
    # ------------------------------------------------------------------

    def _sample_ep(self) -> dict:
        pos = self.rng.uniform(-5, 5, 3).tolist()
        theta = float(self.rng.uniform(0, math.pi))
        e_photon = ELECTRON_MASS_MEV + self.beam_energy_mev / 2
        return {
            "type": "annihilation",
            "process": "e+e-→2γ",
            "photon_count": 2,
            "photon_energy_mev": e_photon,
            "angle_rad": theta,
            "position": pos,
            "energy_mev": 2 * e_photon,
        }

    def _sample_pp_bar(self) -> dict:
        n_pions = int(self.rng.integers(3, 8))
        n_pi0 = max(1, n_pions // 3)
        total_e = 2 * PROTON_MASS_MEV + self.beam_energy_mev
        pos = self.rng.uniform(-5, 5, 3).tolist()
        return {
            "type": "annihilation",
            "process": f"p+p̄→{n_pions}π→γ",
            "pion_count": n_pions,
            "photon_count": 2 * n_pi0,
            "position": pos,
            "energy_mev": total_e * 0.999,
        }

    # ------------------------------------------------------------------
    # Batch runner (called repeatedly from WebSocket handler)
    # ------------------------------------------------------------------

    def run_batch(self, batch_size: int = 500) -> dict:
        batch_energy = 0.0
        batch_ann = 0
        batch_ph = 0
        batch_col = 0
        batch_events: list[dict] = []

        for _ in range(batch_size):
            if not self.running:
                break

            batch_col += 1

            if self.sim_type == "electron_positron":
                gamma = 1 + self.beam_energy_mev / ELECTRON_MASS_MEV
                ann_prob = min(0.3, 1 / (gamma + 1))
                if self.rng.random() < ann_prob:
                    ev = self._sample_ep()
                    batch_energy += ev["energy_mev"]
                    batch_ann += 1
                    batch_ph += ev["photon_count"]
                    batch_events.append(ev)
            else:
                ann_prob = min(0.2, 1 / (1 + self.beam_energy_mev / PROTON_MASS_MEV))
                if self.rng.random() < ann_prob:
                    ev = self._sample_pp_bar()
                    batch_energy += ev["energy_mev"]
                    batch_ann += 1
                    batch_ph += ev["photon_count"]
                    batch_events.append(ev)

        self.collisions += batch_col
        self.annihilations += batch_ann
        self.photons += batch_ph
        self.total_energy_mev += batch_energy
        self.step += batch_size
        self.events = batch_events[-20:]

        energy_j = self.total_energy_mev * MEV_TO_JOULES
        progress = min(self.step / self.total_steps * 100, 100.0)

        return {
            "step": self.step,
            "total_steps": self.total_steps,
            "collisions_computed": self.collisions,
            "annihilations": self.annihilations,
            "photons_produced": self.photons,
            "total_energy_released_mev": self.total_energy_mev,
            "total_energy_released_joules": energy_j,
            "energy_kilotons_tnt": energy_j / TNT_JOULES_PER_KILOTON,
            "particles_remaining": max(0, self.particle_count - self.annihilations),
            "progress_percent": progress,
            "current_events": self.events,
            "complete": self.step >= self.total_steps,
        }