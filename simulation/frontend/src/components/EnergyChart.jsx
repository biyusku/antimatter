import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { useSimStore } from "../store/simulationStore";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-2 text-xs font-mono">
      <div className="text-gray-400 mb-1">Step {label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
        </div>
      ))}
    </div>
  );
}

export default function EnergyChart() {
  const { steps } = useSimStore();

  if (steps.length < 2) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-2">
        <span className="text-gray-400 font-mono text-xs uppercase tracking-wider">
          Energy over Time
        </span>
        <div className="flex-1 flex items-center justify-center h-40 text-gray-600 text-sm font-mono">
          Start simulation to see energy curve
        </div>
      </div>
    );
  }

  const data = steps.map((s, i) => ({
    step: s.step ?? i,
    energyMev: +(s.total_energy_released_mev ?? 0).toFixed(2),
    annihilations: s.annihilations ?? 0,
    photons: s.photons_produced ?? 0,
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3">
      <span className="text-gray-400 font-mono text-xs uppercase tracking-wider">
        Energy over Time
      </span>

      <ResponsiveContainer width="100%" height={180}>
        <LineChart
          data={data}
          margin={{ top: 4, right: 8, left: -10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="step"
            stroke="#374151"
            tick={{ fill: "#6b7280", fontSize: 10 }}
            label={{
              value: "Step",
              position: "insideBottom",
              fill: "#4b5563",
              fontSize: 10,
            }}
          />
          <YAxis stroke="#374151" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{
              fontSize: 10,
              color: "#9ca3af",
              fontFamily: "monospace",
            }}
          />
          <Line
            type="monotone"
            dataKey="energyMev"
            name="Energy (MeV)"
            stroke="#00f5ff"
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="annihilations"
            name="Annihilations"
            stroke="#ff4d6d"
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={120}>
        <LineChart
          data={data}
          margin={{ top: 4, right: 8, left: -10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="step"
            stroke="#374151"
            tick={{ fill: "#6b7280", fontSize: 10 }}
          />
          <YAxis stroke="#374151" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="photons"
            name="Photons"
            stroke="#fbbf24"
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
