import { useState } from "react";
import { Atom, BarChart3, FlaskConical } from "lucide-react";
import SimulationControls from "./components/SimulationControls";
import SimulationStats from "./components/SimulationStats";
import EnergyChart from "./components/EnergyChart";
import ParticleCanvas from "./components/ParticleCanvas";
import Comparator from "./components/Comparator";

const TABS = [
  { id: "simulation", label: "Simulation", Icon: Atom },
  { id: "comparator", label: "Comparator", Icon: BarChart3 },
  { id: "science", label: "Science", Icon: FlaskConical },
];

function ScienceTab() {
  const topics = [
    {
      title: "PET Scanning",
      subtitle: "Antimatter in everyday medicine",
      facts: [
        "F-18 half-life: 109.77 minutes",
        "Antimatter per scan: ~3 nanograms",
        "Gamma ray energy: exactly 511 keV",
        "Angle between gammas: exactly 180°",
        "~8–12 million PET scans per year globally",
      ],
      color: "border-blue-500/40",
      accent: "text-blue-400",
    },
    {
      title: "Antiproton Therapy",
      subtitle: "CERN ACE Experiment (2003–2013)",
      facts: [
        "Bragg peak: dose deposited precisely at tumor",
        "Annihilation bonus: pion shower at Bragg peak",
        "RBE: 4–5× vs proton therapy at Bragg peak",
        "Not clinically available — requires CERN-scale accelerator",
        "Carbon ion therapy fills clinical high-LET niche",
      ],
      color: "border-red-500/40",
      accent: "text-red-400",
    },
    {
      title: "ALPHA-g Gravity Test",
      subtitle: "Nature, September 2023",
      facts: [
        "First direct measurement of gravity on antimatter",
        "Result: antihydrogen FALLS DOWN",
        "g_anti / g_matter = 1.00 ± 0.30",
        "Rules out antigravity as explanation for matter–antimatter asymmetry",
        "CPT symmetry: 1S-2S matches hydrogen to ~12 parts per trillion",
      ],
      color: "border-purple-500/40",
      accent: "text-purple-400",
    },
    {
      title: "Baryon Asymmetry",
      subtitle: "The deepest unsolved problem",
      facts: [
        "~1 extra baryon per 10⁹ pairs survived the Big Bang",
        "Sakharov conditions: B-violation + CP violation + non-equilibrium",
        "Standard Model CP violation is ~10¹⁰× too small",
        "Leptogenesis via heavy right-handed neutrinos: leading candidate",
        "Active experiments: T2K, NOvA, DUNE, LHCb, Belle II",
      ],
      color: "border-yellow-500/40",
      accent: "text-yellow-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
      {topics.map(({ title, subtitle, facts, color, accent }) => (
        <div
          key={title}
          className={`bg-gray-900 border ${color} rounded-xl p-5`}
        >
          <div className={`font-semibold text-sm mb-0.5 ${accent}`}>
            {title}
          </div>
          <div className="text-gray-500 text-xs font-mono mb-3">{subtitle}</div>
          <ul className="space-y-1.5">
            {facts.map((f) => (
              <li
                key={f}
                className="flex items-start gap-2 text-xs text-gray-400 font-mono"
              >
                <span className={`mt-0.5 ${accent}`}>›</span>
                {f}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState("simulation");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="p-1.5 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
            <Atom size={20} className="text-cyan-400" />
          </div>
          <div>
            <div className="font-semibold text-sm text-gray-100 leading-none">
              Antimatter Simulation Platform
            </div>
            <div className="text-xs text-gray-500 font-mono mt-0.5">
              Open-source · Monte Carlo · Real physics
            </div>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="max-w-7xl mx-auto px-4 flex gap-1 pb-0">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-mono border-b-2 transition-colors ${
                activeTab === id
                  ? "border-cyan-400 text-cyan-400"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === "simulation" && (
          <div
            className="grid gap-4"
            style={{ gridTemplateColumns: "280px 1fr 280px" }}
          >
            {/* Left: controls */}
            <div className="flex flex-col gap-4">
              <SimulationControls />
            </div>

            {/* Center: 3D canvas + chart */}
            <div className="flex flex-col gap-4">
              <ParticleCanvas />
              <EnergyChart />
            </div>

            {/* Right: stats */}
            <div className="flex flex-col gap-4">
              <SimulationStats />
            </div>
          </div>
        )}

        {activeTab === "comparator" && (
          <div className="py-2">
            <Comparator />
          </div>
        )}

        {activeTab === "science" && (
          <div className="py-2">
            <ScienceTab />
          </div>
        )}
      </main>
    </div>
  );
}
