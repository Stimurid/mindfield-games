# Mindfield VM Deploy Handoff

**Target:** `mindfield.mindkampf.ru` on the existing VM `moderbober-prod-01` (81.26.176.248).
**Pattern:** identical contour to Quinta — Caddy + basic_auth + `moderbober_default` Docker network, plus one extra container (Python API) and a SQLite volume.
**Status:** all files in this repo are committed; **two manual steps remain on the VM** (DNS, first install). Listed at the bottom.

---

## Architecture

```
Internet
  │
  ├─ :80/:443 → moderbober-caddy   (shared, already running)
  │              ├─ moderbober.mindkampf.ru → moderbober containers
  │              ├─ whitecrow.mindkampf.ru  → whitecrow-static
  │              ├─ quinta.mindkampf.ru     → quinta-static
  │              └─ mindfield.mindkampf.ru  ─┐
  │                                          │
  └─ Docker network: moderbober_default      │
                                             ▼
                       ┌──────────────┐  ┌──────────────────┐
                       │ /api/*       │  │ /*               │
                       │ → mindfield- │  │ → mindfield-     │
                       │   api:8000   │  │   static:80      │
                       │ (uvicorn,    │  │ (nginx:alpine,   │
                       │  FastAPI,    │  │  Vite dist)      │
                       │  SQLite)     │  │                  │
                       └──────┬───────┘  └──────────────────┘
                              │
                              ▼
              /opt/mindfield/data/mindfield.db (bind mount, persistent)
```

Mindfield differs from Quinta in two ways:

1. **Two containers, not one** — there is a real Python API behind the static SPA. Caddy does path routing.
2. **A persistent SQLite volume** — sessions, profiles, materials live there. The deploy script must NEVER wipe `/opt/mindfield/data`.

---

## VM directory layout

```
/opt/mindfield/
├── repo/                    ← git clone of Stimurid/mindfield-games (main)
├── data/                    ← SQLite (mindfield.db) — bind-mounted into api container, never wiped
├── secrets/
│   └── api.env              ← MINDFIELD_LLM_API_KEY=sk-... (chmod 600, root:deploy)
├── bin/
│   ├── deploy               ← copy from repo: deploy/bin/deploy
│   ├── status               ← copy from repo: deploy/bin/status
│   └── backup               ← copy from repo: deploy/bin/backup
├── logs/
│   ├── deploy.log
│   └── backup.log
├── backups/                 ← tarballs of data/ + compose, max 10, made by `backup`
└── docker-compose.yml       ← copy from repo: deploy/docker-compose.yml
```

---

## Containers

| Property | mindfield-api | mindfield-static |
|---|---|---|
| Image | built from `backend/Dockerfile` (python:3.13-slim + uvicorn) | built from `frontend/Dockerfile` (multistage node→nginx:alpine) |
| Network | `moderbober_default` | `moderbober_default` |
| Volumes | `/opt/mindfield/data:/data` (SQLite) | none |
| Env | `env_file: /opt/mindfield/secrets/api.env` plus `MINDFIELD_LLM=openai_compatible`, `MINDFIELD_LLM_API_BASE=https://api.302.ai/v1`, `MINDFIELD_DB=/data/mindfield.db` | none |
| Exposed | none — Caddy internal only | none — Caddy internal only |
| Healthcheck | `curl /api/games` | `wget /` |

---

## Caddy block

To append to `/opt/moderbober/Caddyfile`, then reload Caddy. Snippet lives in [deploy/Caddyfile.snippet](../deploy/Caddyfile.snippet) — replace `<bcrypt-hash>` with the same hash already used for the other sites:

```
mindfield.mindkampf.ru {
    basicauth * {
        timur <bcrypt-hash>
    }
    handle /api/* { reverse_proxy mindfield-api:8000 }
    handle        { reverse_proxy mindfield-static:80 }
}
```

After editing the Caddyfile:

```bash
docker exec moderbober-caddy caddy reload --config /etc/caddy/Caddyfile
```

---

## DNS

| Record | Type | Value |
|---|---|---|
| `mindfield.mindkampf.ru` | A | `81.26.176.248` |

---

## TLS / Auth

- TLS auto-provisioned by Caddy (Let's Encrypt), same as the other sites.
- basic_auth same credentials as moderbober/quinta/whitecrow — reuse the existing hash, do not invent a new one.
- Expected response without creds: `401 Unauthorized`.

---

## Deploy flow

```
push to Stimurid/mindfield-games main
  → GH Actions (.github/workflows/deploy-mindfield.yml)
  → ssh deploy@81.26.176.248
  → /opt/mindfield/bin/deploy
      1. git fetch + reset --hard origin/main
      2. docker compose up -d --build   (rebuilds only changed images)
      3. healthcheck api (curl /api/games inside container) — must be 200
      4. healthcheck web (wget / inside container) — must be 200
      5. edge probe https://mindfield.mindkampf.ru/ — must be 401
      6. /api/llm/models sanity log (does NOT call 302.ai)
  → status --short report
```

The SQLite file at `/opt/mindfield/data/mindfield.db` is **never touched by deploy**. To wipe state on purpose: `docker stop mindfield-api && rm /opt/mindfield/data/mindfield.db && /opt/mindfield/bin/deploy`.

---

## Security notes

1. **302.ai key lives ONLY in `/opt/mindfield/secrets/api.env`** — `chmod 600`, owned by `root:deploy`, never committed to repo, never injected into the static bundle.
2. **No ports exposed to host** — Caddy is the single edge; basic_auth gates everything.
3. **Read-only frontend container** — nginx serves from a baked-in `dist/`, no write surface.
4. **SQLite volume bind-mounted** — survives container rebuild and recreation; backed up by `/opt/mindfield/bin/backup`.
5. **No sudo in deploy** — runs as `deploy` user; docker socket access is the only privileged surface.
6. **Frontend bundle never carries an API key** — provider runs server-side only.

---

## Shared resources (DO NOT MODIFY)

| Resource | Owner | Notes |
|---|---|---|
| `/opt/moderbober/` | ModerBober | Caddyfile lives here |
| `moderbober-caddy` | ModerBober | shared edge container |
| `moderbober_default` | Docker | shared network |
| Ports 80, 443 | Caddy | do not bind from Mindfield |
| `/opt/quinta/`, `/opt/whitecrow/` | other projects | untouched |

---

## Maintenance

```bash
# Status
/opt/mindfield/bin/status                  # full
/opt/mindfield/bin/status --short          # one-line, used by CI

# Manual deploy
/opt/mindfield/bin/deploy

# Dry plan
/opt/mindfield/bin/deploy --dry

# Backup (last 10 kept)
/opt/mindfield/bin/backup

# Logs
tail -50 /opt/mindfield/logs/deploy.log
docker logs mindfield-api --tail 100
docker logs mindfield-static --tail 100

# Recreate containers from template
cd /opt/mindfield && docker compose up -d --build

# Reload Caddy after editing Caddyfile
docker exec moderbober-caddy caddy reload --config /etc/caddy/Caddyfile

# Inspect SQLite (read-only, while api is running)
docker exec -it mindfield-api sqlite3 /data/mindfield.db '.tables'
```

---

## First-install checklist (manual, one time, on the VM)

This is the only out-of-repo work. Everything else flows from GH Actions.

1. **DNS** — add `A mindfield.mindkampf.ru → 81.26.176.248`. Wait for propagation.

2. **Directories**
   ```bash
   sudo mkdir -p /opt/mindfield/{repo,data,secrets,bin,logs,backups}
   sudo chown -R deploy:deploy /opt/mindfield
   ```

3. **302.ai key**
   ```bash
   sudo install -o root -g deploy -m 640 /dev/stdin /opt/mindfield/secrets/api.env <<EOF
   MINDFIELD_LLM_API_KEY=sk-...the real 302.ai key...
   EOF
   ```

4. **Clone repo** (use the same deploy key that Quinta uses, or a fresh read-only deploy key)
   ```bash
   sudo -u deploy git clone git@github.com:Stimurid/mindfield-games.git /opt/mindfield/repo
   ```

5. **Copy compose + bin scripts into their canonical locations**
   ```bash
   sudo -u deploy cp /opt/mindfield/repo/deploy/docker-compose.yml /opt/mindfield/
   sudo -u deploy install -m 750 /opt/mindfield/repo/deploy/bin/deploy  /opt/mindfield/bin/
   sudo -u deploy install -m 750 /opt/mindfield/repo/deploy/bin/status  /opt/mindfield/bin/
   sudo -u deploy install -m 750 /opt/mindfield/repo/deploy/bin/backup  /opt/mindfield/bin/
   ```

6. **Caddy block** — append `deploy/Caddyfile.snippet` content to `/opt/moderbober/Caddyfile`, substitute the real basic_auth hash from the existing block above it, then:
   ```bash
   docker exec moderbober-caddy caddy reload --config /etc/caddy/Caddyfile
   ```

7. **First deploy**
   ```bash
   /opt/mindfield/bin/deploy
   ```
   Expect: build of both images (~2 min first time), then status table with `api=running`, `web=running`, `edge=401`.

8. **GitHub Actions secrets** — same as Quinta. If they already exist on the repo (`PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`, optional `PROD_PORT`), the workflow will fire on the next push. Otherwise add them in repo settings.

9. **Sanity from your laptop**
   ```bash
   curl -sI https://mindfield.mindkampf.ru/                              # → 401
   curl -sI -u timur:<pass> https://mindfield.mindkampf.ru/              # → 200
   curl -s  -u timur:<pass> https://mindfield.mindkampf.ru/api/games     # → JSON, 4 games
   curl -s  -u timur:<pass> https://mindfield.mindkampf.ru/api/llm/models | jq .provider
                                                                         # → "OpenAICompatibleProvider"
   ```

---

## What is NOT deployed in this contour

- Real Anthropic provider — 302.ai is the only path.
- Mock provider — backend defaults to live now; mock stays for unit tests only.
- Cross-game profile aggregation, replay material generator, marketplace, auth UI — Phase 4+.
- Cron backups — `backup` runs manually for now; promote to cron once humans actually play.
