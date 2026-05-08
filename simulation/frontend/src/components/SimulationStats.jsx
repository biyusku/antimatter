import { useSimStore } from "../store/simulationStore";

export default function SimulationStats() {
  const { stats, isComplete, progressPercent } = useSimStore();

  const rows = [
    {
      label: "Annihilations",
      value: (stats.annihilations ?? 0).toLocaleString(),
      color: "text-red-400",
    },
    {
      label: "Energy (MeV)",
      value: (stats.energy ?? 0).toFixed(4),
      color: "text-purple-400",
    },
    {
      label: "Particles",
      value: (stats.particleCount ?? 0).toLocaleString(),
      color: "text-blue-400",
    },
    {
      label: "Step",
      value: (stats.step ?? 0).toLocaleString(),
      color: "text-cyan-400",
    },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-gray-400 font-mono text-xs uppercase tracking-wider">
          Live Statistics
        </span>
        {isComplete && (
          <span className="text-xs font-mono text-green-400 border border-green-800 bg-green-900/30 px-2 py-0.5 rounded">
            Complete
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        {rows.map(({ label, value, color }) => (
          <div key={label} className="bg-gray-800 rounded-lg p-2.5">
            <div className="text-gray-500 text-xs font-mono mb-1">{label}</div>
            <div className={`font-mono font-semibold text-sm ${color}`}>
              {value}
            </div>
          </div>
        ))}
      </div>

      <div>
        <div className="flex justify-between text-xs text-gray-500 font-mono mb-1.5">
          <span>Progress</span>
          <span>{(progressPercent ?? 0).toFixed(1)}%</span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan-500 rounded-full transition-all duration-150"
            style={{ width: `${progressPercent ?? 0}%` }}
          />
        </div>
      </div>
    </div>
  );
}
