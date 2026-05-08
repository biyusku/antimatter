import asyncio
import json
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from app.physics import SimulationEngine

logger = logging.getLogger(__name__)

BROADCAST_INTERVAL = 0.05  # 50ms
DT = 1e-9  # physics time step (seconds)


async def simulation_ws(websocket: WebSocket) -> None:
    await websocket.accept()

    engine: Optional[SimulationEngine] = None
    running: bool = False

    # Mutable containers so inner coroutines can rebind them
    state: dict = {"engine": None, "running": False}

    async def receive_loop() -> None:
        while True:
            raw = await websocket.receive_text()
            msg: dict = json.loads(raw)
            action = msg.get("action", "")

            if action == "start":
                scenario = msg.get("scenario", "electron_positron")
                if state["engine"] is None:
                    state["engine"] = SimulationEngine(scenario)
                state["running"] = True

            elif action == "stop":
                state["running"] = False

            elif action == "reset":
                state["running"] = False
                if state["engine"] is not None:
                    state["engine"].reset()

            elif action == "setScenario":
                scenario = msg.get("scenario", "electron_positron")
                state["running"] = False
                state["engine"] = SimulationEngine(scenario)

    async def broadcast_loop() -> None:
        while True:
            await asyncio.sleep(BROADCAST_INTERVAL)
            if not state["running"]:
                continue
            engine: Optional[SimulationEngine] = state["engine"]
            if engine is None:
                continue

            snapshot = engine.step(dt=DT)

            stats = snapshot["stats"]
            await websocket.send_text(
                json.dumps({
                    "particles": snapshot["particles"],
                    "stats": {
                        "annihilationCount": stats["annihilation_count"],
                        "totalEnergy": stats["total_energy"],
                        "particleCount": stats["particle_count"],
                        "matterCount": stats.get("matter_count", 0),
                        "antimatterCount": stats.get("antimatter_count", 0),
                        "step": stats.get("step", 0),
                    },
                    "timestamp": snapshot["timestamp"],
                })
            )

    receive_task = asyncio.create_task(receive_loop())
    broadcast_task = asyncio.create_task(broadcast_loop())

    try:
        done, pending = await asyncio.wait(
            {receive_task, broadcast_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        for task in done:
            exc = task.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                logger.error("WebSocket task error: %s", exc)
    finally:
        state["running"] = False
        if not receive_task.done():
            receive_task.cancel()
        if not broadcast_task.done():
            broadcast_task.cancel()