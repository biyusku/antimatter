import { useSimStore } from "../store/simulationStore";

export default function SimulationStats() {
  const {
    totalCollisions,
    totalAnnihilations,
    totalPhotons,
    totalEnergyMev,
    energyKilotons,
    progressPercent,
    steps,
    isComplete,
  } = useSimStore();

  const last = steps[steps.length - 1];
  const rate = last?.statistics?.annihilation_rate ?? null;

  const stats = [
    {
      label: "Collisions",
      value: totalCollisions.toLocaleString(),
      color: "text-blue-400",
    },
    {
      label: "Annihilations",
      value: totalAnnihilations.toLocaleString(),
      color: "text-red-400",
    },
    {
      label: "Photons",
      value: totalPhotons.toLocaleString(),
      color: "text-yellow-400",
    },
    {
      label: "Energy (MeV)",
      value: totalEnergyMev.toFixed(2),
      color: "text-purple-400",
    },
    {
      label: "Kilotons TNT",
      value: energyKilotons.toExponential(3),
      color: "text-cyan-400",
    },
    {
      label: "Annihil. Rate",
      value: rate !== null ? `${rate.toFixed(1)}/step` : "—",
      color: "text-green-400",
    },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-4">
      {/* Header */}
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

      {/* Stat grid */}
      <div className="grid grid-cols-2 gap-2">
        {stats.map(({ label, value, color }) => (
          <div key={label} className="bg-gray-800 rounded-lg p-2.5">
            <div className="text-gray-500 text-xs font-mono mb-1">{label}</div>
            <div className={`font-mono font-semibold text-sm ${color}`}>
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 font-mono mb-1.5">
          <span>Progress</span>
          <span>{progressPercent.toFixed(1)}%</span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan-500 rounded-full transition-all duration-150"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Last step info */}
      {last && (
        <div className="border-t border-gray-800 pt-3">
          <div className="text-gray-600 text-xs font-mono mb-2">Last Step</div>
          <div className="space-y-1">
            {[
              ["Step", last.step ?? "—"],
              ["Events", (last.current_events?.length ?? 0).toString()],
              [
                "Efficiency",
                last.statistics?.efficiency != null
                  ? `${(last.statistics.efficiency * 100).toFixed(1)}%`
                  : "—",
              ],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between text-xs font-mono">
                <span className="text-gray-600">{k}</span>
                <span className="text-gray-300">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
