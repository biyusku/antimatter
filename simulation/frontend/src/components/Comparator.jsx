import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const C2 = 8.987551787e16; // J/kg
const KILOTON_J = 4.184e12;
const HIROSHIMA_KT = 15;
const TSAR_KT = 50000;

function calcEnergy(grams) {
  const massKg = (grams * 2) / 1000; // matter + antimatter
  const joules = massKg * C2;
  const kilotons = joules / KILOTON_J;
  return {
    grams,
    energy_joules: joules,
    energy_kilotons_tnt: kilotons,
    hiroshima_multiples: kilotons / HIROSHIMA_KT,
    tsar_bomba_fraction: kilotons / TSAR_KT,
  };
}

const PRESETS = [
  { label: "1 ng", grams: 1e-9, color: "#60a5fa" },
  { label: "1 µg", grams: 1e-6, color: "#34d399" },
  { label: "1 mg", grams: 1e-3, color: "#fbbf24" },
  { label: "1 g", grams: 1, color: "#f87171" },
  { label: "1 kg", grams: 1000, color: "#ff4d6d" },
];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 text-xs font-mono">
      <div className="text-cyan-400 font-semibold mb-1">{d.label}</div>
      <div className="text-gray-300">{d.value.toFixed(2)} kt TNT</div>
    </div>
  );
}

export default function Comparator() {
  const [grams, setGrams] = useState(1);
  const [selected, setSelected] = useState(null);

  const custom = useMemo(() => calcEnergy(grams), [grams]);

  const chartData = PRESETS.map((p) => {
    const e = calcEnergy(p.grams);
    return { label: p.label, value: e.energy_kilotons_tnt, color: p.color };
  });

  const highlights = [
    {
      label: "Kilotons TNT",
      value: custom.energy_kilotons_tnt.toExponential(3),
      color: "text-cyan-400",
    },
    {
      label: "Hiroshimas",
      value: `${custom.hiroshima_multiples.toFixed(4)}×`,
      color: "text-red-400",
    },
    {
      label: "Tsar Fraction",
      value: `${(custom.tsar_bomba_fraction * 100).toFixed(6)}%`,
      color: "text-orange-400",
    },
    { label: "Efficiency", value: "99.9%", color: "text-green-400" },
  ];

  return (
    <div className="flex flex-col gap-6 max-w-3xl mx-auto">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="text-gray-400 font-mono text-xs uppercase tracking-wider mb-4">
          Energy Comparator — E = mc²
        </div>

        {/* Preset buttons */}
        <div className="flex gap-2 flex-wrap mb-4">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => {
                setGrams(p.grams);
                setSelected(p.label);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors ${
                selected === p.label
                  ? "border-cyan-500 bg-cyan-500/10 text-cyan-300"
                  : "border-gray-700 text-gray-400 hover:border-gray-500"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Custom slider */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 font-mono mb-1.5">
            <span>Antimatter mass</span>
            <span className="text-cyan-400">
              {grams >= 1000
                ? `${(grams / 1000).toFixed(2)} kg`
                : grams >= 1
                  ? `${grams.toFixed(3)} g`
                  : grams >= 1e-3
                    ? `${(grams * 1000).toFixed(3)} mg`
                    : grams >= 1e-6
                      ? `${(grams * 1e6).toFixed(3)} µg`
                      : `${(grams * 1e9).toFixed(3)} ng`}
            </span>
          </div>
          <input
            type="range"
            min={-9}
            max={3}
            step={0.01}
            value={Math.log10(grams)}
            onChange={(e) => {
              setGrams(Math.pow(10, parseFloat(e.target.value)));
              setSelected(null);
            }}
            className="w-full accent-cyan-400 h-1"
          />
          <div className="flex justify-between text-xs text-gray-600 font-mono mt-1">
            <span>1 ng</span>
            <span>1 µg</span>
            <span>1 mg</span>
            <span>1 g</span>
            <span>1 kg</span>
          </div>
        </div>

        {/* Highlight stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          {highlights.map(({ label, value, color }) => (
            <div key={label} className="bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 font-mono mb-1">
                {label}
              </div>
              <div className={`font-mono font-semibold text-sm ${color}`}>
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bar chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="text-gray-400 font-mono text-xs uppercase tracking-wider mb-3">
          Preset Comparison (kilotons TNT)
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 10, right: 24, top: 4, bottom: 4 }}
          >
            <XAxis
              type="number"
              stroke="#374151"
              tick={{ fill: "#6b7280", fontSize: 10 }}
              tickFormatter={(v) =>
                v >= 1e6
                  ? `${(v / 1e6).toFixed(0)}Mt`
                  : v >= 1000
                    ? `${(v / 1000).toFixed(0)}kt`
                    : `${v.toFixed(0)}kt`
              }
            />
            <YAxis
              type="category"
              dataKey="label"
              stroke="#374151"
              tick={{ fill: "#9ca3af", fontSize: 11, fontFamily: "monospace" }}
              width={36}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((entry) => (
                <Cell key={entry.label} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* E = mc² working */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 font-mono text-xs text-gray-500">
        <div className="text-gray-300 mb-2">E = mc² calculation</div>
        <div>c² = 8.988 × 10¹⁶ J/kg</div>
        <div>
          mass = {((grams * 2) / 1000).toExponential(3)} kg (matter +
          antimatter)
        </div>
        <div className="text-cyan-400 mt-1">
          E = {custom.energy_joules.toExponential(4)} J{"  "}={" "}
          {custom.energy_kilotons_tnt.toExponential(4)} kilotons TNT
        </div>
      </div>
    </div>
  );
}
