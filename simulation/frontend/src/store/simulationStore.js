import { create } from "zustand";

const DEFAULT_CONFIG = {
  simulation_type: "electron_positron",
  particle_count: 1000,
  monte_carlo_steps: 10000,
  beam_energy_mev: 1.0,
};

// Max visual particles per species (instanced mesh capacity in ParticleCanvas)
const MAX_VISUAL = 300;

let flashId = 0;

export const useSimStore = create((set) => ({
  isRunning: false,
  isComplete: false,
  steps: [],
  events: [],
  flashes: [],
  initConfig: null,
  totalCollisions: 0,
  totalAnnihilations: 0,
  totalPhotons: 0,
  totalEnergyMev: 0,
  energyKilotons: 0,
  progressPercent: 0,
  config: DEFAULT_CONFIG,
  wsConnected: false,

  // Visual / control state required by the task spec
  particles: [],
  stats: { annihilations: 0, energy: 0, particleCount: 0, step: 0 },
  speed: 1.0,
  selectedScenario: DEFAULT_CONFIG.simulation_type,

  setConfig: (c) => set((s) => ({ config: { ...s.config, ...c } })),

  setParticles: (particles) => set({ particles }),
  updateStats: (stats) => set((s) => ({ stats: { ...s.stats, ...stats } })),
  toggleRunning: () => set((s) => ({ isRunning: !s.isRunning })),
  setSpeed: (speed) => set({ speed }),
  setScenario: (selectedScenario) =>
    set((s) => ({
      selectedScenario,
      config: { ...s.config, simulation_type: selectedScenario },
    })),

  startSimulation: () =>
    set((s) => {
      const half = Math.min(
        Math.floor(s.config.particle_count / 2),
        MAX_VISUAL,
      );
      return {
        isRunning: true,
        isComplete: false,
        steps: [],
        events: [],
        flashes: [],
        initConfig: { matterCount: half, antimatterCount: half },
        totalCollisions: 0,
        totalAnnihilations: 0,
        totalPhotons: 0,
        totalEnergyMev: 0,
        energyKilotons: 0,
        progressPercent: 0,
      };
    }),

  stopSimulation: () => set({ isRunning: false }),

  completeSimulation: () => set({ isRunning: false, isComplete: true }),

  updateStep: (d) =>
    set((s) => ({
      steps: [...s.steps.slice(-200), d],
      events: [...s.events.slice(-400), ...(d.current_events || [])],
      totalCollisions: d.collisions_computed ?? s.totalCollisions,
      totalAnnihilations: d.annihilations ?? s.totalAnnihilations,
      totalPhotons: d.photons_produced ?? s.totalPhotons,
      totalEnergyMev: d.total_energy_released_mev ?? s.totalEnergyMev,
      energyKilotons: d.energy_kilotons_tnt ?? s.energyKilotons,
      progressPercent: d.progress_percent ?? s.progressPercent,
    })),

  addFlash: (position) =>
    set((s) => ({
      flashes: [...s.flashes, { id: ++flashId, position }],
    })),

  removeFlash: (id) =>
    set((s) => ({ flashes: s.flashes.filter((f) => f.id !== id) })),

  recordAnnihilation: () =>
    set((s) => ({ totalAnnihilations: s.totalAnnihilations + 1 })),

  setWsConnected: (v) => set({ wsConnected: v }),

  reset: () =>
    set({
      isRunning: false,
      isComplete: false,
      steps: [],
      events: [],
      flashes: [],
      initConfig: null,
      totalCollisions: 0,
      totalAnnihilations: 0,
      totalPhotons: 0,
      totalEnergyMev: 0,
      energyKilotons: 0,
      progressPercent: 0,
    }),
}));
