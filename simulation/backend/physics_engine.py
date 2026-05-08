"""
Antimatter Simulation — Physics Engine
Real QED formulas for pair annihilation, Compton scattering, and pair production.
All constants from CODATA 2018. All formulas from Heitler / Peskin & Schroeder.
"""

from __future__ import annotations
import math

# ── Physical constants (CODATA 2018) ────────────────────────────────────────
C                        = 299_792_458.0          # speed of light, m/s
C_SQUARED                = C * C                  # m²/s²
ELECTRON_MASS_KG         = 9.1093837015e-31       # kg
PROTON_MASS_KG           = 1.67262192369e-27      # kg
ELECTRON_MASS_MEV        = 0.51099895000          # MeV/c²
PROTON_MASS_MEV          = 938.27208816           # MeV/c²
CLASSICAL_ELECTRON_RADIUS = 2.8179403227e-15      # m  (r_e)
JOULES_PER_MEV           = 1.602176634e-13        # J · MeV⁻¹
JOULES_PER_GEV           = JOULES_PER_MEV * 1e3

# Thomson cross section: σ_T = (8π/3) r_e²
_r_e_cm = CLASSICAL_ELECTRON_RADIUS * 100         # m → cm
THOMSON_CROSS_SECTION_CM2 = (8 * math.pi / 3) * _r_e_cm ** 2   # ≈ 6.6524e-25 cm²

# Breit-Wheeler peak: σ_BW_max ≈ 1.70 × 10⁻²⁵ cm² at E_γ ≈ 1.5 m_e c²
# (stored for quick sanity checks)
_BW_PEAK_APPROX_CM2 = 1.70e-25


# ── Physics Engine ────────────────────────────────────────────────────────────

class PhysicsEngine:
    """
    QED physics for the Anti Madde simulation.
    All public methods are pure functions (no side effects).
    """

    # ── E = mc² ──────────────────────────────────────────────────────────────

    def mass_to_energy(self, mass_kg: float) -> float:
        """
        Rest energy via Einstein's mass-energy equivalence.

        Args:
            mass_kg: rest mass in kilograms.

        Returns:
            Energy in Joules.
        """
        return mass_kg * C_SQUARED

    # ── Annihilation energy breakdown ─────────────────────────────────────────

    def annihilation_energy(
        self,
        matter_kg: float,
        antimatter_kg: float | None = None,
    ) -> dict:
        """
        Complete energy breakdown for matter-antimatter annihilation.
        The annihilated mass equals min(matter_kg, antimatter_kg);
        100 % of that mass converts to energy (perfect E = mc² conversion).

        Args:
            matter_kg:    mass of matter particle(s) in kg.
            antimatter_kg: mass of antimatter in kg. Defaults to matter_kg
                           (symmetric collision).

        Returns:
            dict with keys:
              annihilated_mass_kg        — mass destroyed per side (kg)
              total_annihilated_mass_kg  — total mass → energy (kg)
              matter_remaining_kg        — leftover matter (kg)
              antimatter_remaining_kg    — leftover antimatter (kg)
              energy_joules              — total energy released (J)
              energy_mev                 — total energy in MeV
              energy_gev                 — total energy in GeV
              energy_tev                 — total energy in TeV
              energy_kwh                 — energy in kilowatt-hours
              energy_tnt_kg              — TNT equivalent in kg
              energy_tnt_metric_tons     — TNT equivalent in metric tons
              hiroshima_equivalents      — ratio to Little Boy bomb (~6.3×10¹³ J)
              photon_energy_each_mev     — energy per annihilation photon (e⁺e⁻→2γ)
              mass_to_energy_efficiency  — always 1.0 (100 %)
              cern_ad_production_years   — years for CERN AD to produce annihilated_mass
        """
        if antimatter_kg is None:
            antimatter_kg = matter_kg

        annihilated   = min(matter_kg, antimatter_kg)
        total_mass_kg = annihilated * 2             # both sides contribute

        energy_j   = self.mass_to_energy(total_mass_kg)
        energy_mev = energy_j / JOULES_PER_MEV
        energy_gev = energy_mev / 1_000
        energy_tev = energy_gev / 1_000
        energy_kwh = energy_j  / 3.6e6
        energy_tnt_kg  = energy_j / 4.184e6         # 1 kg TNT = 4.184 MJ
        energy_tnt_ton = energy_tnt_kg / 1_000

        hiroshima  = energy_j / 6.3e13              # Little Boy ≈ 6.3×10¹³ J

        # CERN AD: ~5×10⁷ antiprotons/min, ~180 days/year operational
        ad_antiprotons_per_year = 5e7 * 60 * 24 * 180
        cern_ad_years = (annihilated / PROTON_MASS_KG) / ad_antiprotons_per_year

        # e⁺e⁻ → 2γ: each photon carries half the rest energy
        photon_mev = energy_mev / 2 if energy_mev > 0 else 0.0

        return {
            "annihilated_mass_kg":       annihilated,
            "total_annihilated_mass_kg": total_mass_kg,
            "matter_remaining_kg":       matter_kg - annihilated,
            "antimatter_remaining_kg":   antimatter_kg - annihilated,
            "energy_joules":             energy_j,
            "energy_mev":                energy_mev,
            "energy_gev":                energy_gev,
            "energy_tev":                energy_tev,
            "energy_kwh":                energy_kwh,
            "energy_tnt_kg":             energy_tnt_kg,
            "energy_tnt_metric_tons":    energy_tnt_ton,
            "hiroshima_equivalents":     hiroshima,
            "photon_energy_each_mev":    photon_mev,
            "mass_to_energy_efficiency": 1.0,
            "cern_ad_production_years":  cern_ad_years,
        }

    # ── Klein-Nishina cross section ───────────────────────────────────────────

    def klein_nishina_cross_section(self, energy_mev: float) -> float:
        """
        Total Klein-Nishina cross section for Compton scattering of a photon
        off a free electron at rest.

        Formula (Heitler, The Quantum Theory of Radiation, 3rd ed., §26):

            ε = E_γ / (m_e c²)

            σ_KN = (3 σ_T / 4) {
                [(1+ε)/ε³] · [2ε(1+ε)/(1+2ε) − ln(1+2ε)]
                + ln(1+2ε)/(2ε)
                − (1+3ε)/(1+2ε)²
            }

        Limits:
          ε → 0  (low energy):  σ_KN → σ_T  (Thomson limit, ~6.65×10⁻²⁵ cm²)
          ε → ∞  (high energy): σ_KN ∝ ln(2ε)/ε  (falls off as 1/E_γ)

        Args:
            energy_mev: incident photon energy in MeV.

        Returns:
            Total cross section in cm² per electron.
            Returns 0 for non-positive energies.
        """
        if energy_mev <= 0:
            return 0.0

        eps = energy_mev / ELECTRON_MASS_MEV        # dimensionless: E_γ / m_e c²

        if eps < 1e-9:                              # deep Thomson regime
            return THOMSON_CROSS_SECTION_CM2

        one_2eps  = 1.0 + 2.0 * eps
        ln_1_2eps = math.log(one_2eps)

        term_a = ((1.0 + eps) / eps ** 3) * (
            (2.0 * eps * (1.0 + eps) / one_2eps) - ln_1_2eps
        )
        term_b = ln_1_2eps / (2.0 * eps)
        term_c = (1.0 + 3.0 * eps) / (one_2eps ** 2)

        sigma = (3.0 * THOMSON_CROSS_SECTION_CM2 / 4.0) * (term_a + term_b - term_c)
        return max(sigma, 0.0)

    # ── Breit-Wheeler cross section ───────────────────────────────────────────

    def breit_wheeler_cross_section(self, energy_mev: float) -> float:
        """
        Total Breit-Wheeler cross section for two-photon pair production:
            γ + γ → e⁺ + e⁻

        Assumes two identical photons colliding head-on in the lab frame,
        so the centre-of-mass energy is W = 2 E_γ.

        Formula (Breit & Wheeler, Phys. Rev. 46, 1087, 1934):

            β = √(1 − (m_e c² / E_γ)²)

            σ_BW = (π r_e² / 2)(1 − β²) ·
                   [2β(β² − 2) + (3 − β⁴) ln((1+β)/(1−β))]

        Threshold: E_γ = m_e c² = 0.511 MeV  (so W_threshold = 1.022 MeV).
        Below threshold, cross section is identically zero.
        Peak: σ_BW ≈ 1.70×10⁻²⁵ cm² at E_γ ≈ 1.5 × m_e c² ≈ 0.77 MeV.

        Args:
            energy_mev: energy of each photon in MeV.

        Returns:
            Cross section in cm².
            Returns 0 at or below threshold (0.511 MeV).
        """
        THRESHOLD_MEV = ELECTRON_MASS_MEV           # 0.511 MeV per photon

        if energy_mev <= THRESHOLD_MEV:
            return 0.0

        ratio = ELECTRON_MASS_MEV / energy_mev      # m_e c² / E_γ
        beta2 = 1.0 - ratio * ratio                 # β² = 1 − (m_e/E_γ)²
        if beta2 <= 0.0:
            return 0.0

        beta = math.sqrt(beta2)
        if beta >= 1.0:
            return 0.0

        log_term = math.log((1.0 + beta) / (1.0 - beta))   # = 2 arctanh(β)
        bracket  = 2.0 * beta * (beta2 - 2.0) + (3.0 - beta2 * beta2) * log_term

        sigma = (math.pi / 2.0) * (_r_e_cm ** 2) * (1.0 - beta2) * bracket
        return max(sigma, 0.0)

    # ── Relativistic kinematics helpers ──────────────────────────────────────

    def gamma_factor(self, velocity_ms: float) -> float:
        """Lorentz factor γ = 1/√(1−β²).  Returns inf if |v| ≥ c."""
        beta = velocity_ms / C
        if abs(beta) >= 1.0:
            return math.inf
        return 1.0 / math.sqrt(1.0 - beta * beta)

    def kinetic_energy_relativistic(self, mass_kg: float, velocity_ms: float) -> float:
        """Relativistic kinetic energy KE = (γ−1) m c²  in Joules."""
        g = self.gamma_factor(velocity_ms)
        if math.isinf(g):
            return math.inf
        return (g - 1.0) * self.mass_to_energy(mass_kg)

    def doppler_shift(self, freq_hz: float, velocity_ms: float, angle_rad: float = 0.0) -> float:
        """
        Relativistic Doppler shift for a source moving at velocity_ms.
        angle_rad = 0 means source moving directly toward the observer.

        f_obs = f_src × √((1 + β cos θ) / (1 − β²))
        """
        beta = velocity_ms / C
        cos_theta = math.cos(angle_rad)
        gamma = self.gamma_factor(velocity_ms)
        return freq_hz * gamma * (1.0 + beta * cos_theta)

    def de_broglie_wavelength(self, mass_kg: float, velocity_ms: float) -> float:
        """de Broglie wavelength λ = h / (γmv)  in metres."""
        PLANCK_H = 6.62607015e-34   # J·s
        gamma = self.gamma_factor(velocity_ms)
        momentum = gamma * mass_kg * velocity_ms
        if momentum == 0:
            return math.inf
        return PLANCK_H / momentum

    def pair_production_threshold_mev(self) -> float:
        """
        Minimum photon energy for Breit-Wheeler pair production
        (two identical photons, head-on collision).
        Returns 0.511 MeV = m_e c².
        """
        return ELECTRON_MASS_MEV

    def positronium_lifetime_s(self, spin_state: str = "para") -> float:
        """
        Theoretical ground-state positronium lifetime.
          para-Ps  (singlet, S=0):  τ ≈ 125 ps  (decays → 2γ)
          ortho-Ps (triplet, S=1):  τ ≈ 142 ns  (decays → 3γ)

        Args:
            spin_state: "para" or "ortho".

        Returns:
            Lifetime in seconds.
        """
        if spin_state.lower() == "ortho":
            return 142.0e-9    # 142 ns
        return 125.0e-12       # 125 ps


# ── Module-level singleton ────────────────────────────────────────────────────
physics_engine = PhysicsEngine()