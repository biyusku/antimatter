from fastapi import APIRouter

router = APIRouter(prefix="/api/simulations", tags=["simulations"])

SIMULATION_TYPES = [
    {
        "id": "electron_positron",
        "name": "Electron-Positron Annihilation",
        "formula": "e⁺ + e⁻ → 2γ",
        "photon_energy_kev": 511,
        "description": (
            "Classic QED annihilation. Each photon carries exactly 511 keV "
            "(the electron rest-mass energy). Cross-section follows Klein-Nishina formula."
        ),
        "min_energy_mev": 0.511,
    },
    {
        "id": "proton_antiproton",
        "name": "Proton-Antiproton Annihilation",
        "formula": "p + p̄ → ~5π → γ + ν",
        "photon_energy_kev": None,
        "description": (
            "Produces ~5 pions on average (π⁺, π⁻, π⁰). "
            "π⁰ → 2γ quickly; π± cascade to muons then electrons + neutrinos. "
            "~2/3 of energy recoverable as photons/leptons."
        ),
        "min_energy_mev": 938.3,
    },
    {
        "id": "pair_production",
        "name": "Pair Production",
        "formula": "γ → e⁺ + e⁻  (near nucleus)",
        "photon_energy_kev": None,
        "description": (
            "Reverse of e⁺e⁻ annihilation. Requires photon energy ≥ 1.022 MeV "
            "(2 × electron rest mass). Occurs in the Coulomb field of a nucleus."
        ),
        "min_energy_mev": 1.022,
    },
]


@router.get("/types")
async def simulation_types() -> list:
    return SIMULATION_TYPES


@router.get("/types/{sim_id}")
async def simulation_type_detail(sim_id: str) -> dict:
    for t in SIMULATION_TYPES:
        if t["id"] == sim_id:
            return t
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Simulation type '{sim_id}' not found")