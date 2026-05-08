from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/physics", tags=["physics"])

# Physical constants
C = 2.99792458e8
C_SQ = C ** 2
TNT_KT = 4.184e12
TNT_MT = 4.184e15
ELECTRON_MASS_MEV = 0.51099895
PROTON_MASS_MEV = 938.27208816
MEV_TO_J = 1.602176634e-13
N_A = 6.02214076e23
LITTLE_BOY_YIELD_KT = 15.0
TSAR_YIELD_MT = 50.0


class AnnihilationRequest(BaseModel):
    matter_grams: float
    antimatter_grams: Optional[float] = None


@router.post("/annihilation")
async def calculate_annihilation(req: AnnihilationRequest) -> dict:
    m1 = req.matter_grams / 1000
    m2 = (req.antimatter_grams if req.antimatter_grams is not None else req.matter_grams) / 1000
    total_mass = m1 + m2
    energy_j = total_mass * C_SQ * 0.999
    energy_mev = energy_j / MEV_TO_J
    energy_kt = energy_j / TNT_KT
    energy_mt = energy_kt / 1000
    fission_j_per_kg = 202.5 * MEV_TO_J * N_A / 235.0
    equiv_u235_kg = energy_j / fission_j_per_kg
    return {
        "matter_grams": req.matter_grams,
        "antimatter_grams": req.antimatter_grams or req.matter_grams,
        "total_mass_grams": total_mass * 1000,
        "energy_joules": energy_j,
        "energy_mev": energy_mev,
        "energy_kilotons_tnt": energy_kt,
        "energy_megatons_tnt": energy_mt,
        "efficiency_percent": 99.9,
        "hiroshima_multiples": energy_kt / LITTLE_BOY_YIELD_KT,
        "tsar_bomba_fraction": energy_mt / TSAR_YIELD_MT,
        "equivalent_fission_kg_uranium": equiv_u235_kg,
        "photon_energy_kev": 511.0,
    }


@router.get("/compare")
async def compare_weapons() -> dict:
    ann_2g_j = 2e-3 * C_SQ * 0.999
    ann_2g_kt = ann_2g_j / TNT_KT
    tsar_j = TSAR_YIELD_MT * TNT_MT
    needed_total_kg = tsar_j / (C_SQ * 0.999)
    return {
        "comparisons": [
            {
                "name": "Little Boy (Hiroshima 1945)",
                "type": "Fission U-235",
                "fissile_mass_kg": 64,
                "mass_converted_g": 0.7,
                "yield_kilotons": 15.0,
                "efficiency_percent": 0.0011,
                "color": "#ef4444",
            },
            {
                "name": "Tsar Bomba (USSR 1961)",
                "type": "Thermonuclear Fusion",
                "total_mass_kg": 27000,
                "mass_converted_g": 2300,
                "yield_kilotons": 50000,
                "yield_megatons": 50.0,
                "efficiency_percent": 0.0085,
                "color": "#f97316",
            },
            {
                "name": "1g Matter + 1g Antimatter",
                "type": "Annihilation (E=mc²)",
                "total_mass_g": 2.0,
                "mass_converted_g": 2.0,
                "yield_kilotons": ann_2g_kt,
                "yield_megatons": ann_2g_kt / 1000,
                "efficiency_percent": 99.9,
                "hiroshima_multiples": ann_2g_kt / LITTLE_BOY_YIELD_KT,
                "color": "#00f5ff",
            },
        ],
        "to_match_tsar_bomba": {
            "antimatter_needed_kg": needed_total_kg / 2,
            "antimatter_needed_g": (needed_total_kg / 2) * 1000,
        },
        "production_reality": {
            "cern_annual_production_grams": 3.3e-14,
            "total_ever_produced_grams": 1e-8,
            "van_allen_belt_natural_grams": 1.6e-4,
            "years_to_produce_1g": 1 / 3.3e-14,
            "cost_per_gram_usd": 6.25e16,
        },
    }


@router.get("/production-calculator")
async def production_calculator(target_grams: float = 1.0) -> dict:
    cern_gpy = 3.3e-14
    return {
        "target_grams": target_grams,
        "years_at_cern_rate": target_grams / cern_gpy,
        "universe_ages": (target_grams / cern_gpy) / 1.38e10,
        "estimated_cost_usd": target_grams * 6.25e16,
        "cern_annual_production_grams": cern_gpy,
        "total_ever_produced_grams": 1e-8,
    }


@router.get("/pet-scanner")
async def pet_scanner_physics() -> dict:
    return {
        "principle": "Positron Emission Tomography",
        "isotope": "F-18 (Fluorine-18)",
        "half_life_minutes": 109.8,
        "decay": "Beta-plus → positron → travels ~1mm → annihilates → 2γ at 511 keV",
        "photon_energy_kev": 511,
        "photons_opposite_directions": True,
        "antimatter_per_scan_grams": 1e-12,
        "scanners_worldwide": 15000,
        "scans_per_year_global": 4_000_000,
        "resolution_mm": 4,
        "notes": "uEXPLORER whole-body PET achieves 40x sensitivity gain over conventional scanners",
    }