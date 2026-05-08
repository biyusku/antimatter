# Antimatter Simulation Platform

An open-source physics simulation engine for visualizing and computing antimatter interactions — pair production, annihilation, baryon asymmetry, and more.

---

## Quick Start (No Coding Required)

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/antimatter-sim.git
cd antimatter-sim/simulation

# 2. Start everything
docker compose up

# 3. Open your browser
#    API:  http://localhost:8000
#    Docs: http://localhost:8000/docs
#    App:  http://localhost:5173
```

To stop: press `Ctrl+C`, then `docker compose down`.

---

## What This Is

This platform lets you:

- **Simulate** electron-positron annihilation and pair production in real time
- **Visualize** particle trajectories in configurable magnetic fields (like Anderson's 1932 cloud chamber)
- **Calculate** exact energy outputs for matter-antimatter reactions (E = mc²)
- **Explore** the baryon asymmetry problem with interactive CP-violation models
- **Share** your simulations with a public link

It is built for students, science communicators, and physicists who want an interactive, browser-based tool — no installation, no Python required to use it.

---

## Architecture

```
simulation/
├── backend/          FastAPI (Python) — physics engine + REST API
│   ├── app/
│   │   ├── main.py       API entrypoint
│   │   ├── config.py     Environment settings
│   │   ├── physics/      Simulation modules (annihilation, pair production, ...)
│   │   ├── api/          REST route handlers
│   │   ├── db/           Database models and migrations (PostgreSQL)
│   │   └── auth/         GitHub OAuth + JWT authentication
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         React + Vite — interactive UI and visualization
├── docker-compose.yml
└── .gitignore
```

**Services:**

| Service  | Port | Purpose                                |
| -------- | ---- | -------------------------------------- |
| backend  | 8000 | FastAPI REST API + WebSocket           |
| frontend | 5173 | React web application                  |
| db       | 5432 | PostgreSQL (simulation results, users) |
| redis    | 6379 | Job queue + caching                    |

---

## Configuration

Copy the example env file and edit as needed:

```bash
cp backend/.env.example backend/.env
```

For GitHub OAuth (optional — enables saving and sharing simulations):

1. Go to GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. Set callback URL to `http://localhost:8000/auth/github/callback`
3. Copy the Client ID and Secret into `backend/.env`

---

## Contributing

Contributions are welcome! To run the backend with hot-reload outside Docker:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Physics modules live in `backend/app/physics/`. Each simulation type is a self-contained module. Adding a new simulation means adding a module there and registering a route in `backend/app/api/`.

Please open an issue before submitting large PRs.

---

## License

MIT — free to use, modify, and distribute.

---

_Built for the Anti Madde Turkish science documentary project._
