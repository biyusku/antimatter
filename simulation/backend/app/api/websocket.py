import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.physics.engine import SimulationRunner

logger = logging.getLogger(__name__)


async def simulation_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    runner: SimulationRunner | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "start_simulation":
                params = msg.get("params", {})
                runner = SimulationRunner(params)
                await websocket.send_text(
                    json.dumps({"type": "simulation_started", "params": params})
                )

                while runner.running and runner.step < runner.total_steps:
                    result = runner.run_batch(batch_size=500)
                    await websocket.send_text(
                        json.dumps({"type": "simulation_update", "data": result})
                    )
                    if result["complete"]:
                        break

                await websocket.send_text(
                    json.dumps({
                        "type": "simulation_complete",
                        "data": {
                            "total_annihilations": runner.annihilations,
                            "total_energy_mev": runner.total_energy_mev,
                            "photons_produced": runner.photons,
                        },
                    })
                )

            elif msg.get("type") == "stop_simulation":
                if runner:
                    runner.running = False
                await websocket.send_text(json.dumps({"type": "simulation_stopped"}))

    except WebSocketDisconnect:
        if runner:
            runner.running = False
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if runner:
            runner.running = False