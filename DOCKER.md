# Docker Compose deployment

## Start

Docker Compose reads `.env` for non-secret variable substitution when the file
exists. Backend-only settings such as `LLM_API_KEY` and `EMBEDDING_API_KEY` can be
placed in an optional `.env.docker` file. Both files are ignored by Git; never
commit real passwords or API keys.

```powershell
Copy-Item .env.example .env.docker
```

The `DATABASE_URL` inside the backend container is set by Compose and points to
the `postgres` service. It intentionally overrides any `DATABASE_URL` in
`.env.docker`.

```powershell
docker compose up --build -d
docker compose ps
```

Services are available at:

- Frontend: <http://localhost:3000>
- Backend: <http://localhost:8000>
- Health check: <http://localhost:8000/health>

The browser-facing API URL defaults to `http://localhost:8000`. Override it at
build time with `NEXT_PUBLIC_API_BASE_URL` when deploying to another host:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "https://api.example.com"
docker compose build frontend
docker compose up -d
```

## Database initialization

Container startup intentionally does not run migrations or seed data. Review and
run these commands explicitly when initializing or upgrading a database:

```powershell
docker compose exec backend python -m alembic -c alembic.ini upgrade head
docker compose exec backend python backend/scripts/seed_demo.py
```

The migration command changes the database schema. Back up important data and
review pending migrations before running it outside a disposable local setup.

## Verify and stop

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
Invoke-WebRequest http://localhost:3000 -UseBasicParsing
docker compose down
```

`docker compose down` removes the containers and network but preserves the named
`postgres_data` volume. Only `docker compose down -v` removes that database
volume.
