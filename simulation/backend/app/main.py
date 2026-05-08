import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.physics import router as physics_router
from app.api.routes.simulation import router as sim_router
from app.api.websocket import simulation_ws
from app.auth.github import router as auth_router
from app.config import settings
from app.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database...")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Antimatter Simulation Platform",
    description="Open-source physics simulation engine for antimatter interactions.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(physics_router)
app.include_router(sim_router)
app.include_router(auth_router)


@app.websocket("/ws/simulate")
async def ws_simulate(websocket: WebSocket) -> None:
    await simulation_ws(websocket)


@app.get("/")
async def root() -> dict:
    return {
        "name": "Antimatter Simulation Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}