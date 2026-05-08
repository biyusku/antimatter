"""
Monte Carlo annihilation simulation engine.

Supports electron-positron and proton-antiproton annihilation.
Designed to be called in batches from a WebSocket handler so
progress can be streamed to the frontend in real time.
"""

import math
from typing import Any

import numpy as np

MEV_TO_J = 1.602176634e-13
TNT_KT = 4.184e12
ELECTRON_MASS_MEV = 0.51099895
PROTON_MASS_MEV = 938.27208816
R_E = 2.8179403227e-15  # classical electron radius, metres


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
    # Cross-section helpers
    # ------------------------------------------------------------------

    def klein_nishina_cs(self, energy_mev: float) -> float:
        """Approximate Klein-Nishina total cross-section (cm²)."""
        epsilon = energy_mev / ELECTRON_MASS_MEV
        if epsilon < 1e-6:
            return (8 / 3) * math.pi * R_E ** 2 * 1e4  # Thomson limit, cm²
        ln_term = math.log(1 + 2 * epsilon)
        cs = (
            2
            * math.pi
            * R_E ** 2
            * (
                (1 + epsilon) / epsilon ** 2
                * (2 * (1 + epsilon) / (1 + 2 * epsilon) - ln_term / epsilon)
                + ln_term / (2 * epsilon)
                - (1 + 3 * epsilon) / (1 + 2 * epsilon) ** 2
            )
        )
        return abs(cs) * 1e4  # m² → cm²

    # ------------------------------------------------------------------
    # Single-event samplers
    # ------------------------------------------------------------------

    def _sample_ep(self) -> dict:
        """Sample one e⁺e⁻ annihilation event."""
        pos = self.rng.uniform(-5, 5, 3).tolist()
        theta = float(self.rng.uniform(0, math.pi))
        e_photon = ELECTRON_MASS_MEV + self.beam_energy_mev / 2
        return {
            "type": "annihilation",
            "process": "e⁺+e⁻→2γ",
            "photon_count": 2,
            "photon_energy_mev": e_photon,
            "angle_rad": theta,
            "position": pos,
            "energy_mev": 2 * e_photon,
        }

    def _sample_pp_bar(self) -> dict:
        """Sample one p+p̄ annihilation event (average pion multiplicity)."""
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

        energy_j = self.total_energy_mev * MEV_TO_J
        progress = min(self.step / self.total_steps * 100, 100.0)

        return {
            "step": self.step,
            "total_steps": self.total_steps,
            "collisions_computed": self.collisions,
            "annihilations": self.annihilations,
            "photons_produced": self.photons,
            "total_energy_released_mev": self.total_energy_mev,
            "total_energy_released_joules": energy_j,
            "energy_kilotons_tnt": energy_j / TNT_KT,
            "particles_remaining": max(0, self.particle_count - self.annihilations),
            "progress_percent": progress,
            "current_events": self.events,
            "complete": self.step >= self.total_steps,
        }