# Mindfield API — FastAPI + SQLite, served by uvicorn on internal :8000.
# Caddy on the VM terminates TLS and basic_auth and reverse-proxies here.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MINDFIELD_DB=/data/mindfield.db

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY game_genomes ./game_genomes
COPY seed_materials ./seed_materials
COPY seed_materials_real ./seed_materials_real
# Library corpus + phase docs are bind-mounted at runtime from
# /opt/mindfield/repo/docs into /docs (see deploy/docker-compose.yml).

# /data is bind-mounted from /opt/mindfield/data on the host so SQLite
# survives container restarts. Created here so first boot does not race.
RUN mkdir -p /data && chmod 770 /data
VOLUME ["/data"]

EXPOSE 8000

# No CMD-time secrets. MINDFIELD_LLM_API_KEY is injected via the host
# env_file at /opt/mindfield/secrets/api.env.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/games >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
