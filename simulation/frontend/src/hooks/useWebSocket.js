import { useEffect, useRef, useCallback } from "react";
import { useSimStore } from "../store/simulationStore";

const WS_BASE =
  import.meta.env?.VITE_WS_URL ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

const MEV_TO_JOULES = 1.602176634e-13;

export function useWebSocket() {
  const ws = useRef(null);
  const {
    updateStats,
    completeSimulation,
    setWsConnected,
    setParticles,
    config,
  } = useSimStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const s = new WebSocket(WS_BASE + "/ws/simulate");
    ws.current = s;

    s.onopen = () => setWsConnected(true);
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
          updateStats({
            annihilations: m.stats?.annihilationCount ?? 0,
            energy: (m.stats?.totalEnergy ?? 0) / MEV_TO_JOULES,
            particleCount: m.stats?.particleCount ?? 0,
            step: m.stats?.step ?? 0,
          });
        } else if (m.type === "simulation_complete") {
          completeSimulation();
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };
  }, [updateStats, completeSimulation, setWsConnected, setParticles]);

  const startSim = useCallback(() => {
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
