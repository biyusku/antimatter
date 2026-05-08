"""
NIST CODATA 2018 physical constants for antimatter simulation.
All values verified against NIST official database.
"""

# Speed of light (exact by definition)
C = 2.99792458e8          # m/s
C_SQUARED = C ** 2        # m2/s2

# Planck constants
H    = 6.62607015e-34     # J*s (exact)
HBAR = 1.054571817e-34    # J*s

# Elementary charge (exact)
E_CHARGE = 1.602176634e-19  # C

# Particle masses (kg)
ELECTRON_MASS   = 9.1093837015e-31   # kg
PROTON_MASS     = 1.67262192369e-27  # kg
NEUTRON_MASS    = 1.67492749804e-27  # kg
POSITRON_MASS   = ELECTRON_MASS      # same as electron
ANTIPROTON_MASS = PROTON_MASS        # same as proton

# Particle masses (MeV/c2) -- particle physics standard units
ELECTRON_MASS_MEV      = 0.51099895      # MeV/c2
PROTON_MASS_MEV        = 938.27208816    # MeV/c2
NEUTRON_MASS_MEV       = 939.56542052    # MeV/c2
PION_CHARGED_MASS_MEV  = 139.57039       # MeV/c2  pi+/-
PION_NEUTRAL_MASS_MEV  = 134.9768        # MeV/c2  pi0
MUON_MASS_MEV          = 105.6583755     # MeV/c2  mu+/-

# Energy conversions
MEV_TO_JOULES          = 1.602176634e-13   # J per MeV
JOULES_TO_MEV          = 1 / MEV_TO_JOULES
TNT_JOULES_PER_TON     = 4.184e9
TNT_JOULES_PER_KILOTON = 4.184e12
TNT_JOULES_PER_MEGATON = 4.184e15

# Annihilation photon energy (e+e- -> 2 gamma)
ANNIHILATION_PHOTON_ENERGY_MEV = ELECTRON_MASS_MEV   # 0.511 MeV = 511 keV
ANNIHILATION_PHOTON_ENERGY_J   = ANNIHILATION_PHOTON_ENERGY_MEV * MEV_TO_JOULES

# QED constants
ALPHA      = 7.2973525693e-3    # fine structure constant (dimensionless)
R_E        = 2.8179403262e-15   # classical electron radius (m)
THOMSON_CS = (8 * 3.14159265358979323846 / 3) * R_E ** 2  # m2

# Statistical / thermodynamic
K_B = 1.380649e-23    # Boltzmann constant J/K
N_A = 6.02214076e23   # Avogadro number mol-1

# Nuclear weapons -- verified historical data
LITTLE_BOY_URANIUM_KG        = 64.0      # total HEU in weapon
LITTLE_BOY_YIELD_KT          = 15.0      # kilotons TNT (Hiroshima 1945)
LITTLE_BOY_MASS_CONVERTED_KG = 6.99e-4   # ~0.7 grams converted to energy
LITTLE_BOY_EFFICIENCY        = LITTLE_BOY_MASS_CONVERTED_KG / LITTLE_BOY_URANIUM_KG  # ~0.001%

TSAR_BOMBA_YIELD_MT          = 50.0      # megatons TNT (USSR 1961)
TSAR_BOMBA_DEVICE_MASS_KG    = 27000.0   # total device mass
TSAR_BOMBA_MASS_CONVERTED_KG = 2.3       # kg converted to energy