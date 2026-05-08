import { useEffect, useRef, useCallback } from "react";
import { useSimStore } from "../store/simulationStore";

const WS_BASE =
  import.meta.env?.VITE_WS_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

const MEV_TO_JOULES = 1.602176634e-13;

export function useWebSocket() {
  const ws = useRef(null);
  const frameRef = useRef(0); // monotonic frame counter for chart x-axis
  const {
    updateStats,
    appendEnergyPoint,
    completeSimulation,
    setWsConnected,
    setParticles,
    isRunning,
    config,
  } = useSimStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const s = new WebSocket(WS_BASE + "/ws/simulate");
    ws.current = s;

    s.onopen = () => {
      setWsConnected(true);
      // Auto-start if simulation was already running (e.g. reconnect)
      if (useSimStore.getState().isRunning) {
        const scenario =
          useSimStore.getState().config?.scenario ?? "electron_positron";
        s.send(JSON.stringify({ action: "start", scenario }));
      }
    };
    s.onclose = () => {
      setWsConnected(false);
      setTimeout(connect, 3000);
    };
    s.onerror = (e) => console.error("WebSocket error:", e);
    s.onmessage = (e) => {
      try {
        const m = JSON.parse(e.data);
        if (m.particles !== undefined) {
          setParticles(m.particles);
          const energyMev = (m.stats?.totalEnergy ?? 0) / MEV_TO_JOULES;
          const frame = ++frameRef.current;
          updateStats({
            annihilations: m.stats?.annihilationCount ?? 0,
            energy: energyMev,
            particleCount: m.stats?.particleCount ?? 0,
            step: m.stats?.step ?? frame,
            matterCount: m.stats?.matterCount ?? 0,
            antimatterCount: m.stats?.antimatterCount ?? 0,
          });
          appendEnergyPoint({
            step: frame,
            energy: +energyMev.toFixed(4),
            annihilations: m.stats?.annihilationCount ?? 0,
          });
        } else if (m.type === "simulation_complete") {
          completeSimulation();
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };
  }, [
    updateStats,
    appendEnergyPoint,
    completeSimulation,
    setWsConnected,
    setParticles,
  ]);

  const startSim = useCallback(() => {
    frameRef.current = 0;
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          action: "start",
          scenario: config?.scenario ?? "electron_positron",
        }),
      );
    }
  }, [config]);

  const stopSim = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: "stop" }));
    }
  }, []);

  const resetSim = useCallback(() => {
    frameRef.current = 0;
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: "reset" }));
    }
  }, []);

  const setScenario = useCallback((scenario) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: "setScenario", scenario }));
    }
  }, []);

  const sendControl = useCallback((action, payload = {}) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action, ...payload }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  return { startSim, stopSim, resetSim, setScenario, sendControl };
}
