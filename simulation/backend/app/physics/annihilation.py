"""
Annihilation physics — Phase 1 physics upgrade.

Replaces the simple Dirac non-relativistic cross-section with:
  - Heitler (1954) total cross-section (full relativistic treatment)
  - Klein-Nishina dσ/dΩ for photon angular sampling
  - Full 4-momentum photon production with Lorentz boost to lab frame
  - Singlet-state polarisation anti-correlation (ε₁ · ε₂ = 0)

Physics references:
  - Dirac (1930): Proc. Cambridge Phil. Soc. 26, 361 — NR cross-section
  - Heitler, "Quantum Theory of Radiation" (1954), Oxford, §26 — full σ
  - Klein & Nishina, Z. Phys. 52 (1929): dσ/dΩ = (r_e²/2)(E'/E)²(E'/E + E/E' − sin²θ)
  - Berestetskii, Lifshitz, Pitaevskii, "Quantum Electrodynamics" (1982), §88–89
  - PDG Review of Particle Physics (2022), §40

Heitler total cross-section for e+e- → 2γ (positron Lorentz factor γ_lab in e- rest frame):

    σ = (π r_e² / (γ+1)) × {[(γ²+4γ+1)/(γ²-1)] ln(γ+√(γ²-1)) − (γ+3)/√(γ²-1)}

    NR limit (β → 0):  σ → π r_e² / β_lab ≈ π r_e² c / v_rel  [Dirac 1930] ✓
    UR limit (γ → ∞):  σ → (π r_e² / γ)(ln 2γ − 1)

In the symmetric CM frame each particle has speed β_cm ≈ v_rel/(2c), giving
γ_lab = 2γ²_cm − 1 for the equivalent lab-frame formula.

Annihilation probability per timestep (Poisson first-order):
    P = 1 − exp(−n · σ · v_rel · dt)

Angular distribution (Klein-Nishina, CM frame, E'/E = 1 at threshold):
    dσ/dΩ = (r_e²/2)(1 + cos²θ)
    Sampled by rejection Monte Carlo with ~75 % acceptance efficiency.

Spin correlation (PDG 2022 §40.8):
    Singlet (S=0, para-positronium): ε₁ · ε₂ = 0 (perpendicular polarisations).
    Triplet (S=1, ortho-positronium): φ sampled uniformly.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from .constants import (
    C,
    C_SQUARED,
    ELECTRON_MASS,
    ELECTRON_MASS_MEV,
    MEV_TO_JOULES,
    PROTON_MASS,
    PROTON_MASS_MEV,
    R_E,
    TNT_JOULES_PER_KILOTON,
)

if TYPE_CHECKING:
    from .particles import Particle

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_PI_RE_SQ: float = math.pi * R_E * R_E        # π r_e²  (m²)
_V_MIN: float = 1.0e4                           # m/s — floor to prevent σ → ∞
_BOX_HALF: float = 10.0                         # must match simulation_engine._BOUNDS

# Effective 2-D number density in SI units (m⁻²).
#
# Physical rates for e+e- annihilation are unobservably small at laboratory
# particle densities. To make the simulation visually meaningful we use an
# effective density corresponding to a highly compressed particle beam:
# ~1 particle per (12 pm)² ≈ conditions near a particle collider interaction
# point. This gives P_ann ≈ 0.5 % per timestep at v_rel = 1×10⁶ m/s,
# so a typical pair survives ~200 steps before annihilating — pedagogically
# realistic dynamics without being either instant or invisible.
#
# Derivation:  P ≈ σ_Heitler · v_rel · N · dt  (Poisson first order)
#   target P = 0.005,  v_rel = 1e6 m/s,  dt = 1e-7 s
#   σ(v=1e6) ≈ π r_e² c / v ≈ 7.5e-27 m²
#   N = P / (σ · v · dt) ≈ 6.7e24 m⁻²  → rounded to 7e24 m⁻²
_N_2D: float = 7.0e24                          # m⁻²  (effective pedagogical density)


# ---------------------------------------------------------------------------
# Photon data structure
# ---------------------------------------------------------------------------

@dataclass
class AnnihilationPhoton:
    """
    Fully kinematic description of one annihilation-produced photon.

    Alias: Photon (backward-compatible name, used by produce_photons callers).

    Energies in MeV.  Momenta in MeV/c.  Positions in simulation units.
    4-momentum uses natural units (c = 1): p = [E, px, py, pz], all in MeV.
    Metric signature: (+, -, -, -).
    """
    energy_MeV: float
    momentum_4vec: list           # [E, px, py, pz] in MeV
    direction: list               # unit 3-vector [nx, ny, nz]
    polarization: list            # unit 3-vector ⊥ to direction
    production_vertex: list       # [x, y, z] in simulation units
    theta_cm: float               # CM-frame polar angle (rad)
    correlation_type: str = "singlet"   # 'singlet' (S=0) or 'triplet' (S=1)

    def to_dict(self) -> dict:
        return {
            "energy_MeV":        self.energy_MeV,
            "momentum_4vec":     self.momentum_4vec,
            "direction":         self.direction,
            "polarization":      self.polarization,
            "production_vertex": self.production_vertex,
            "theta_cm":          self.theta_cm,
            "correlation_type":  self.correlation_type,
        }


# Backward-compatible alias
Photon = AnnihilationPhoton


# ---------------------------------------------------------------------------
# Internal geometry helpers
# ---------------------------------------------------------------------------

def _distance_sq(p1: "Particle", p2: "Particle") -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return dx * dx + dy * dy


def _relative_speed(p1: "Particle", p2: "Particle") -> float:
    dvx = p1.vx - p2.vx
    dvy = p1.vy - p2.vy
    return math.sqrt(dvx * dvx + dvy * dvy)


def _heitler_cross_section(v_rel: float) -> float:
    """
    Total e+e- → 2γ cross-section via the Heitler (1954) formula.

    The symmetric CM-frame speed of each particle is β_cm = v_rel / (2c).
    The equivalent lab-frame (one particle at rest) positron Lorentz factor is
    γ_lab = 2γ²_cm − 1.

    NR limit (β_cm → 0) recovers σ = π r_e² c / v_rel  (Dirac 1930). ✓

    Args:
        v_rel: relative speed of the pair (m/s, SI units)

    Returns:
        Total annihilation cross-section (m²).
    """
    v_safe = max(v_rel, _V_MIN)
    beta_cm = v_safe / (2.0 * C)

    # Non-relativistic limit — avoids floating-point issues near γ_lab = 1
    if beta_cm < 1.0e-3:
        return _PI_RE_SQ * C / v_safe

    beta_cm = min(beta_cm, 0.9999)
    gamma_cm = 1.0 / math.sqrt(1.0 - beta_cm * beta_cm)

    # Lab-frame Lorentz factor for the symmetric → asymmetric boost
    gamma_lab = max(2.0 * gamma_cm * gamma_cm - 1.0, 1.0 + 1.0e-8)
    sqrt_g2m1 = math.sqrt(gamma_lab * gamma_lab - 1.0)

    # Heitler (1954) §26 eq. (26.1)
    numerator = (
        (gamma_lab * gamma_lab + 4.0 * gamma_lab + 1.0)
        / (gamma_lab * gamma_lab - 1.0)
        * math.log(gamma_lab + sqrt_g2m1)
        - (gamma_lab + 3.0) / sqrt_g2m1
    )
    sigma = (_PI_RE_SQ / (gamma_lab + 1.0)) * numerator
    return max(sigma, 0.0)


def klein_nishina_total_cross_section(E_cm_MeV: float) -> float:
    """
    Total e+e- annihilation cross-section (m²) — public interface.

    Thin wrapper around _heitler_cross_section that accepts CM energy in MeV.

    Args:
        E_cm_MeV: total CM energy in MeV (minimum 2 × 0.511 MeV).

    Returns:
        Total annihilation cross-section (m²).
    """
    gamma_cm = max(E_cm_MeV / (2.0 * ELECTRON_MASS_MEV), 1.0 + 1.0e-8)
    beta_cm  = math.sqrt(1.0 - 1.0 / (gamma_cm * gamma_cm))
    v_rel    = max(2.0 * beta_cm * C, _V_MIN)
    return _heitler_cross_section(v_rel)


# ---------------------------------------------------------------------------
# Public helpers (task spec §5)
# ---------------------------------------------------------------------------

def lorentz_boost(four_momentum: np.ndarray, beta_vec: np.ndarray) -> np.ndarray:
    """
    Lorentz-boost a 4-momentum vector by velocity β = v/c.

    Convention: p = [E, px, py, pz] in MeV  (natural units c = 1).
    Only the component of 3-momentum parallel to the boost mixes with energy;
    perpendicular components are unchanged.

    Args:
        four_momentum: np.array([E, px, py, pz]) in MeV
        beta_vec:      np.array([βx, βy, βz]) — boost velocity / c, |β| < 1

    Returns:
        Boosted np.array([E', px', py', pz']) in MeV.
    """
    beta_sq = float(np.dot(beta_vec, beta_vec))
    if beta_sq < 1.0e-14:
        return four_momentum.copy()

    beta  = math.sqrt(beta_sq)
    gamma = 1.0 / math.sqrt(max(1.0 - beta_sq, 1.0e-10))

    E = float(four_momentum[0])
    p = four_momentum[1:].astype(float)

    beta_hat = beta_vec / beta
    p_par    = float(np.dot(p, beta_hat))     # component along boost axis
    p_perp   = p - p_par * beta_hat           # perpendicular components (unchanged)

    E_prime     = gamma * (E  - beta * p_par)
    p_par_prime = gamma * (p_par - beta * E)

    return np.array([E_prime, *(p_perp + p_par_prime * beta_hat)])


def sample_klein_nishina_angle(E_cm_MeV: float) -> float:
    """
    Rejection-sample the CM-frame polar angle θ for e+e- → 2γ.

    In the CM frame (E'/E = 1) the Klein-Nishina differential cross-section is:

        dσ/d(cosθ) ∝ (1 + cos²θ)            [threshold regime]

    At relativistic CM energies a forward-peaking factor is included:

        dσ/d(cosθ) ∝ (1 + cos²θ) × (1 + β_cm)/(1 − β_cm cosθ)²

    Rejection envelope for the threshold case: g(cosθ) = 2 (efficiency ≈ 75 %).
    Relativistic case uses a tighter envelope evaluated at cosθ = +1.

    Args:
        E_cm_MeV: total CM energy √s in MeV.

    Returns:
        θ ∈ [0, π] in radians.
    """
    # Each beam particle's CM-frame energy
    epsilon = E_cm_MeV / (2.0 * ELECTRON_MASS_MEV)   # in units of m_e c²

    if epsilon <= 1.0 + 1.0e-4:
        # Threshold: dσ/d(cosθ) ∝ 1 + cos²θ,  envelope = 2
        while True:
            cos_theta = random.uniform(-1.0, 1.0)
            if random.uniform(0.0, 2.0) <= 1.0 + cos_theta * cos_theta:
                return math.acos(cos_theta)

    # Relativistic CM-frame speed of each beam particle
    beta_cm = min(math.sqrt(1.0 - 1.0 / max(epsilon * epsilon, 1.0 + 1.0e-8)), 0.9999)

    # Envelope: w_max at cosθ = +1 → 2(1+β)/(1−β)²
    envelope = 2.0 * (1.0 + beta_cm) / (1.0 - beta_cm) ** 2

    while True:
        cos_theta  = random.uniform(-1.0, 1.0)
        kn_weight  = 1.0 + cos_theta * cos_theta
        rel_factor = (1.0 + beta_cm) / (1.0 - beta_cm * cos_theta) ** 2
        if random.uniform(0.0, envelope) <= kn_weight * rel_factor:
            return math.acos(cos_theta)


def compute_annihilation_probability(
    v_rel: float,
    n_density: float,
    dt: float,
) -> float:
    """
    Per-timestep annihilation probability using the Heitler cross-section.

        P = 1 − exp(−n · σ · v_rel · dt)

    Args:
        v_rel:     relative speed of the pair (m/s)
        n_density: 2-D target number density (sim-unit⁻²)
        dt:        physics timestep (seconds)

    Returns:
        Probability ∈ [0, 1).
    """
    sigma = _heitler_cross_section(v_rel)
    rate  = sigma * max(v_rel, _V_MIN) * n_density
    return 1.0 - math.exp(-rate * dt)


def generate_photon_pair(
    p_matter: "Particle",
    p_anti: "Particle",
) -> tuple["Photon", "Photon"]:
    """
    Generate two photons from e+e- → 2γ with complete 4-momentum kinematics.

    Algorithm:
      1. Build relativistic lab-frame 4-momenta for both particles.
      2. Compute CM-frame boost velocity β_cm = p_total / E_total.
      3. Compute invariant mass √s; floor at 2 m_e c² to stay physical.
      4. Sample CM-frame emission direction (θ, φ) from Klein-Nishina dσ/dΩ.
      5. Assign back-to-back CM-frame 4-momenta (each photon E = √s/2).
      6. Build singlet-state polarisation vectors: ε₁ ⊥ direction₁,
         ε₂ = (direction₂ × ε₁) / |direction₂ × ε₁|  so ε₁ · ε₂ = 0.
      7. Lorentz-boost both photon 4-momenta to lab frame.

    Spin correlation — singlet state (S=0, para-positronium):
      ε₁ · ε₂ = 0  (polarisations are exactly perpendicular).

    Args:
        p_matter: matter particle (electron, is_antimatter=False)
        p_anti:   antimatter particle (positron, is_antimatter=True)

    Returns:
        (photon1, photon2) — back-to-back in CM frame, boosted to lab frame.
    """
    mass  = p_matter.mass
    m_MeV = mass * C_SQUARED / MEV_TO_JOULES    # rest mass in MeV/c²

    vertex = [
        (p_matter.x + p_anti.x) / 2.0,
        (p_matter.y + p_anti.y) / 2.0,
        0.0,
    ]

    # --- Relativistic lab-frame 4-momenta ---
    def _p4(vx: float, vy: float) -> np.ndarray:
        v_sq  = vx * vx + vy * vy
        beta  = math.sqrt(v_sq) / C
        gamma = 1.0 / math.sqrt(max(1.0 - beta * beta, 1.0e-10))
        E_MeV  = gamma * m_MeV
        # p [MeV/c] = γ m v / MEV_TO_JOULES  (SI → natural)
        scale  = gamma * mass * C / MEV_TO_JOULES
        return np.array([E_MeV, vx * scale, vy * scale, 0.0])

    p4_minus = _p4(p_matter.vx, p_matter.vy)   # electron
    p4_plus  = _p4(p_anti.vx,  p_anti.vy)      # positron

    P_total = p4_minus + p4_plus
    E_total = float(P_total[0])

    # Invariant mass √s — floored at 2 m_e c² to keep events physical
    s_val  = E_total * E_total - float(np.dot(P_total[1:], P_total[1:]))
    sqrt_s = math.sqrt(max(s_val, (2.0 * m_MeV) ** 2))

    # CM-frame boost velocity (natural units)
    beta_cm = P_total[1:] / E_total            # shape (3,)

    # --- Each photon carries half the CM energy ---
    E_ph_cm = sqrt_s / 2.0

    # --- Sample emission direction from Klein-Nishina ---
    theta_cm = sample_klein_nishina_angle(sqrt_s)
    phi_cm   = random.uniform(0.0, 2.0 * math.pi)

    sin_t = math.sin(theta_cm)
    cos_t = math.cos(theta_cm)
    cos_p = math.cos(phi_cm)
    sin_p = math.sin(phi_cm)

    n1 = np.array([sin_t * cos_p, sin_t * sin_p, cos_t])
    n2 = -n1   # back-to-back in CM frame

    # CM-frame 4-momenta (massless: |p| = E)
    p1_cm = np.array([E_ph_cm, *(E_ph_cm * n1)])
    p2_cm = np.array([E_ph_cm, *(E_ph_cm * n2)])

    # --- Boost to lab frame ---
    p1_lab = lorentz_boost(p1_cm, beta_cm)
    p2_lab = lorentz_boost(p2_cm, beta_cm)

    def _unit(v: np.ndarray, fallback: np.ndarray) -> np.ndarray:
        nm = float(np.linalg.norm(v))
        return v / nm if nm > 1.0e-30 else fallback

    dir1 = _unit(p1_lab[1:], n1)
    dir2 = _unit(p2_lab[1:], n2)

    # --- Polarisation vectors — singlet state (S=0): ε₁ ⊥ ε₂ ---
    # Build ε₁ perpendicular to dir1 using Gram-Schmidt from a reference axis.
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(dir1, ref))) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    eps1 = _unit(ref - float(np.dot(ref, dir1)) * dir1,
                 np.array([1.0, 0.0, 0.0]))

    # Singlet: ε₂ = dir2 × ε₁,  normalised → ε₁ · ε₂ = 0
    cross = np.cross(dir2, eps1)
    eps2  = _unit(cross, np.cross(dir2, np.array([0.0, 1.0, 0.0])))

    E1_lab = float(p1_lab[0])
    E2_lab = float(p2_lab[0])

    ph1 = AnnihilationPhoton(
        energy_MeV       = E1_lab,
        momentum_4vec    = p1_lab.tolist(),
        direction        = dir1.tolist(),
        polarization     = eps1.tolist(),
        production_vertex= vertex,
        theta_cm         = theta_cm,
        correlation_type = "singlet",
    )
    ph2 = AnnihilationPhoton(
        energy_MeV       = E2_lab,
        momentum_4vec    = p2_lab.tolist(),
        direction        = dir2.tolist(),
        polarization     = eps2.tolist(),
        production_vertex= vertex,
        theta_cm         = math.pi - theta_cm,   # back-to-back
        correlation_type = "singlet",
    )
    return ph1, ph2


# ---------------------------------------------------------------------------
# Public API — called by simulation_engine.py
# ---------------------------------------------------------------------------

def detect_annihilation(
    p1: "Particle",
    p2: "Particle",
    dt: float,
) -> bool:
    """
    Monte Carlo annihilation decision using the Heitler cross-section.

    Replaces the old Dirac NR cross-section with the full relativistic
    Heitler (1954) formula, keeping the identical Poisson probability model:

        P = 1 − exp(−n · σ_Heitler · v_rel · dt)

    The Dirac result is recovered exactly in the NR limit (β → 0).

    Args:
        p1:  matter particle      (is_antimatter=False)
        p2:  antimatter particle  (is_antimatter=True)
        dt:  physics time step in seconds

    Returns:
        True with probability P (Monte Carlo accept/reject).
    """
    if p1.is_antimatter == p2.is_antimatter:
        return False

    v_rel = max(_relative_speed(p1, p2), _V_MIN)
    prob  = compute_annihilation_probability(v_rel, _N_2D, dt)
    return random.random() < prob


def calculate_energy(mass: float) -> dict:
    """
    Calculate rest-mass annihilation energy for a particle–antiparticle pair.

        E = 2 × mass × c²

    Args:
        mass: rest mass of ONE particle (kg).

    Returns:
        dict with energy_joules, energy_mev, energy_kilotons_tnt.
    """
    energy_joules = 2.0 * mass * C_SQUARED
    energy_mev    = energy_joules / MEV_TO_JOULES
    energy_kt     = energy_joules / TNT_JOULES_PER_KILOTON

    return {
        "mass_kg":             mass,
        "energy_joules":       energy_joules,
        "energy_mev":          energy_mev,
        "energy_kilotons_tnt": energy_kt,
    }


def produce_photons(p1: "Particle", p2: "Particle") -> dict:
    """
    Compute photon products of a matter–antimatter annihilation event.

    For e+e- pairs: delegates to generate_photon_pair() for full 4-momentum
    kinematics with Klein-Nishina angular sampling and singlet polarisation.

    For p+p̄ pairs: uses the simplified hadronic cascade model (PDG average:
    4-photon equivalents, ~0.1 % lost to neutrinos).

    The returned dict is JSON-serialisable and backward-compatible with the
    structure simulation_engine.py expects (process, position, photon_count,
    photons list with energy_mev and theta, photon_energy_mev, total_energy_mev).

    Args:
        p1: matter Particle
        p2: antimatter AntiParticle

    Returns:
        dict with process, position, photon_count, photons, photon_energy_mev,
        total_energy_mev, and (for e+e-) full Photon kinematics.
    """
    mass  = p1.mass
    mid_x = (p1.x + p2.x) / 2.0
    mid_y = (p1.y + p2.y) / 2.0

    is_electron = math.isclose(mass, ELECTRON_MASS, rel_tol=1.0e-3)

    if is_electron:
        ph1, ph2 = generate_photon_pair(p1, p2)
        return {
            "process":           "e+e-→2γ",
            "position":          [mid_x, mid_y],
            "photon_count":      2,
            "photons":           [ph1.to_dict(), ph2.to_dict()],
            "photon_energy_mev": (ph1.energy_MeV + ph2.energy_MeV) / 2.0,
            "total_energy_mev":  ph1.energy_MeV + ph2.energy_MeV,
        }

    # p+p̄ → hadronic cascade → ~4 photon equivalents, ~0.1 % to neutrinos
    total_mev = 2.0 * PROTON_MASS_MEV * 0.999
    phi_step  = math.pi / 2.0
    theta_cm  = sample_klein_nishina_angle(total_mev)
    return {
        "process":           "p+p̄→πons→γ",
        "position":          [mid_x, mid_y],
        "photon_count":      4,
        "photons":           [
            {
                "energy_mev": total_mev / 4.0,
                "theta":      theta_cm + i * phi_step,
            }
            for i in range(4)
        ],
        "photon_energy_mev": total_mev / 4.0,
        "total_energy_mev":  total_mev,
    }


# Legacy alias kept for callers that used annihilation_products
annihilation_products = produce_photons