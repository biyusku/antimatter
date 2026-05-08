---
title: Project Memory Index
created: 2026-05-08
tags: [index, agent]
---

# Project Memory Index

AI agent memory for the **Anti Madde** Turkish science documentary project. All research areas and agent-managed notes are linked below.

---

## Research Areas

| #   | Topic                                  | Wiki Note                   | Status       |
| --- | -------------------------------------- | --------------------------- | ------------ |
| 1   | Antimatter basics & history            | [[antimatter_history]]      | **Complete** |
| 2   | Antimatter production (CERN, Fermilab) | [[antimatter_production]]   | **Complete** |
| 3   | Antimatter detection & storage         | [[antimatter-detection]]    | Pending      |
| 4   | Medical & future applications          | [[antimatter_applications]] | **Complete** |
| 5   | Weapons & military research history    | [[antimatter_weapons]]      | **Complete** |

---

## Completed Memory Notes

- [[antimatter_history]] — Dirac equation (1928), Anderson positron discovery (1932), all confirmed antimatter particles, CP violation, Sakharov conditions, energy efficiency calculations (fission/fusion/annihilation), 1g+1g = 43 kt TNT, full timeline 1905–2023.
- [[antimatter_applications]] — PET scanning, antiproton therapy (ACE/CERN), antihydrogen gravity test (ALPHA-g 2023), baryon asymmetry, power generation, laser pair production. Key numbers for script use.
- [[antimatter_weapons]] — Augenstein/RAND 1986 report, ICAN/Penn State ACNPP, NASA NIAC studies, precise energy calculations (1 g ≈ 43 kt TNT), Tsar Bomba comparison (needs 1.16 kg, not milligrams), four impossibility barriers (production/storage/stability/triggering), Angels & Demons verdict, near-term propulsion concepts.

---

## Key Facts Cross-Reference

### PET Scanning (Medical — Area 4)

- Tracer: FDG (¹⁸F-fluorodeoxyglucose), F-18 half-life = **109.77 min**
- Antimatter per scan: ~**3 nanograms** (positron mass)
- Annihilation produces two **511 keV** gamma rays at **180°** — enables 3D coincidence imaging
- ~8–12 million PET scans/year globally
- uEXPLORER: whole-body PET, 40× sensitivity gain

### Antiproton Therapy (Medical — Area 4)

- CERN ACE experiment (2003–2013): RBE **4–5×** vs protons at Bragg peak
- Annihilation bonus: pion shower at tumor site
- **Not clinically available** — requires CERN-scale infrastructure

### Fundamental Science (Area 4)

- ALPHA-g 2023 (_Nature_): antihydrogen **falls DOWN** — gravity same for matter/antimatter
- CPT symmetry: antihydrogen 1S-2S matches hydrogen to **~12 parts per trillion**
- Baryon asymmetry: ~1 extra baryon per 10⁹ pairs; Standard Model CP violation ~10¹⁰× too small

### Future Power (Area 4)

- Annihilation energy density: **9 × 10¹³ MJ/kg** (2 billion × gasoline)
- To power 1M-person city/year: ~9 kg antimatter (theoretical)
- Current cost: ~**$62.5 trillion/gram** — centuries from viability
- Laser pair production (Breit-Wheeler): ELI, LUXE@DESY — 2025–2028 milestones

---

## Project Structure Notes

- Vault root: `E:\Anti Madde\wiki\` (open this folder in Obsidian)
- Agent memory: `wiki/_agent/memory/` — all notes here, linked from this index
- Research documents: `E:\Anti Madde\research\` — detailed source docs (outside vault)
  - `research/01_antimatter_history_physics.md` — full Area 1 research (Dirac, Anderson, timeline, energy calcs)
  - `research/04_medical_future_applications.md` — full Area 4 research
  - `research/03_weapons_military_history.md` — full Area 5 research (weapons & military)
- Filenames: `kebab-case.md`; frontmatter required on all agent-managed files
- Internal links: Obsidian wikilinks `[[note-name]]`

---

## Simulation Platform Status

_Updated: 2026-05-08_

Interactive physics simulation built at `E:\Anti Madde\simulation\` to accompany the documentary.

### Backend — `simulation/backend/app/physics/` (814 lines, all compiled ✓)

| File                   | Lines | Description                                                            |
| ---------------------- | ----- | ---------------------------------------------------------------------- |
| `__init__.py`          | 24    | Public API exports                                                     |
| `particles.py`         | 96    | `Particle` / `AntiParticle` dataclasses, relativistic γ, KE            |
| `annihilation.py`      | 102   | E=mc² energy calc, `detect_annihilation`, gamma ray products           |
| `fields.py`            | 89    | `ElectromagneticField`, Lorentz force, cyclotron radius                |
| `simulation_engine.py` | 225   | `SimulationEngine` with scenarios, Boris push integrator               |
| `engine.py`            | 219   | `SimulationRunner` (Monte Carlo, WebSocket batching) + `PhysicsEngine` |
| `constants.py`         | 59    | All SI constants, TNT conversions, Klein-Nishina constants             |

Smoke test: e⁺e⁻ annihilation → 1.022 MeV ✓. All `.pyc` files present (imports verified).

### REST API Endpoints (working)

- `POST /api/physics/annihilation` — energy from arbitrary matter+antimatter mass
- `GET /api/physics/compare` — Little Boy / Tsar Bomba / annihilation side-by-side
- `GET /api/physics/production-calculator` — CERN-rate cost/time to target mass
- `GET /api/physics/pet-scanner` — PET physics data
- `GET /api/simulations/types` — 3 simulation types with formulas

### WebSocket — `/ws/simulate`

Real-time Monte Carlo streaming: `start_simulation` → batched `simulation_update` events → `simulation_complete`. Supports `stop_simulation`.

### Frontend — `simulation/frontend/src/` (React + Vite + Tailwind)

Three-tab UI: **Simulation** (ParticleCanvas + EnergyChart + SimulationControls + SimulationStats), **Comparator**, **Science** (fact cards for PET / antiproton therapy / ALPHA-g / baryon asymmetry).

### What Remains

- Tests — zero written; `pytest` + `pytest-asyncio` are in `requirements.txt`
- `.env` — copy from `.env.example`; GitHub OAuth Client ID/Secret needed for auth
- `docker compose up` — full stack not yet smoke-tested end-to-end
- `antimatter-detection.md` — wiki note still missing (listed as Pending in index)

---

## Adding New Notes

1. Create file in `wiki/_agent/memory/` with required frontmatter
2. Add entry to the table above and relevant cross-reference section
3. Link from related notes using `[[filename]]`
