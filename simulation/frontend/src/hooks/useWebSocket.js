import { useEffect, useRef, useCallback } from "react";
import { useSimStore } from "../store/simulationStore";

const WS_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_WS_URL) ||
  "ws://localhost:8000";

export function useWebSocket() {
  const ws = useRef(null);
  const { updateStep, completeSimulation, setWsConnected, config } =
    useSimStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const s = new WebSocket(WS_URL + "/ws/simulation");
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
        if (m.type === "simulation_step") updateStep(m.data);
        else if (m.type === "simulation_complete") completeSimulation();
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };
  }, [updateStep, completeSimulation, setWsConnected]);

  const startSim = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({ type: "start_simulation", params: config }),
      );
    }
  }, [config]);

  const stopSim = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "stop_simulation" }));
    }
  }, []);

  const resetSim = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "reset_simulation" }));
    }
  }, []);

  const setScenario = useCallback((scenario) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "set_scenario", scenario }));
    }
  }, []);

  const sendControl = useCallback((type, payload = {}) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, ...payload }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  return { startSim, stopSim, resetSim, setScenario, sendControl };
}
