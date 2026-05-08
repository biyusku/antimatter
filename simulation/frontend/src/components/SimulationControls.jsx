import { Play, Square, RotateCcw, Atom } from "lucide-react";
import { useSimStore } from "../store/simulationStore";
import { useWebSocket } from "../hooks/useWebSocket";

const TYPES = [
  {
    value: "electron_positron",
    label: "e⁺ + e⁻ → 2γ",
    desc: "511 keV · QED · Klein-Nishina",
  },
  {
    value: "proton_antiproton",
    label: "p + p̄ → πions",
    desc: "Hadronic · ~5 pions avg",
  },
  { value: "mixed", label: "Mixed beam", desc: "Multi-species collisions" },
];

const SLIDERS = [
  {
    key: "particle_count",
    label: "Particles",
    min: 100,
    max: 10000,
    step: 100,
    fmt: (v) => v.toLocaleString(),
  },
  {
    key: "monte_carlo_steps",
    label: "MC Steps",
    min: 1000,
    max: 100000,
    step: 1000,
    fmt: (v) => v.toLocaleString(),
  },
  {
    key: "beam_energy_mev",
    label: "Beam Energy (MeV)",
    min: 0.1,
    max: 10.0,
    step: 0.1,
    fmt: (v) => `${v.toFixed(1)} MeV`,
  },
];

export default function SimulationControls() {
  const { config, setConfig, isRunning, wsConnected, reset, startSimulation } =
    useSimStore();
  const { startSim, stopSim } = useWebSocket();

  function handleStart() {
    startSimulation();
    startSim();
  }

  function handleStop() {
    stopSim();
    useSimStore.getState().stopSimulation();
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Atom size={15} className="text-cyan-400" />
        <span className="text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
          Simulation
        </span>
        <div
          className={`ml-auto w-2 h-2 rounded-full ${
            wsConnected ? "bg-green-400 animate-pulse" : "bg-red-500"
          }`}
          title={wsConnected ? "Connected" : "Disconnected"}
        />
      </div>

      {/* Collision type selector */}
      <div className="flex flex-col gap-1.5">
        <span className="text-gray-400 text-xs font-mono uppercase tracking-wider">
          Collision Type
        </span>
        {TYPES.map(({ value, label, desc }) => (
          <button
            key={value}
            onClick={() => setConfig({ simulation_type: value })}
            disabled={isRunning}
            className={`text-left px-3 py-2 rounded-lg border text-xs transition-all duration-150 ${
              config.simulation_type === value
                ? "border-cyan-500 bg-cyan-500/10 text-cyan-300"
                : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
            } disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            <div className="font-mono font-semibold">{label}</div>
            <div className="text-gray-500 mt-0.5">{desc}</div>
          </button>
        ))}
      </div>

      {/* Sliders */}
      <div className="flex flex-col gap-3">
        {SLIDERS.map(({ key, label, min, max, step, fmt }) => (
          <div key={key}>
            <div className="flex justify-between text-xs text-gray-400 mb-1.5 font-mono">
              <span>{label}</span>
              <span className="text-cyan-400">{fmt(config[key])}</span>
            </div>
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={config[key]}
              disabled={isRunning}
              onChange={(e) =>
                setConfig({
                  [key]:
                    key === "beam_energy_mev"
                      ? parseFloat(e.target.value)
                      : parseInt(e.target.value, 10),
                })
              }
              className="w-full accent-cyan-400 h-1 disabled:opacity-40"
            />
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex flex-col gap-2">
        {!isRunning ? (
          <button
            onClick={handleStart}
            disabled={!wsConnected}
            className="flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:cursor-not-allowed text-black font-semibold text-sm py-2.5 rounded-lg transition-colors"
          >
            <Play size={14} />
            Start Simulation
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="flex items-center justify-center gap-2 bg-red-500 hover:bg-red-400 text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
          >
            <Square size={14} />
            Stop
          </button>
        )}
        <button
          onClick={reset}
          disabled={isRunning}
          className="flex items-center justify-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-gray-300 text-sm py-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <RotateCcw size={13} />
          Reset
        </button>
      </div>
    </div>
  );
}
