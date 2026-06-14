# ADTools

This folder contains three separate tools/projects:

- `tulip-master` — network flow analysis and CTF-style traffic inspection platform.
- `LessDestructiveFarm-main` — attack/defense game management web application.
- `firegex-main` — Linux firewall/traffic filtering toolkit with regex and proxy modules.
- `client-attacker` — sploit runner client for farm-compatible APIs.
- `test-flag-checker` — standalone local checker with manual accept/deny UI.

---

## Folder contents

```text
ADTools/
├── tulip-master/
├── LessDestructiveFarm-main/
├── firegex-main/
├── client-attacker/
└── test-flag-checker/
```

---

## 1)🌷 tulip-master 🌷

### What it does
Tulip is a traffic analysis stack with:
- flow ingestion/import components,
- API services,
- frontend UI for viewing and comparing flows,
- database schema/services (Timescale/PostgreSQL-based components).

### How to run
From the project folder:

```bash
cd /home/tuna/ADTools/tulip-master
```

Docker Compose run:
```bash
docker compose up -d
```

---

## 2)🐧 LessDestructiveFarm-main 🐧

### What it does
LessDestructiveFarm is a game/farm management service with:
- backend API and GraphQL schema/resolvers,
- Next.js frontend dashboard,
- game logic (`game/`) and archived props (`game-archive-props/`).

### How to run
From the project folder:

```bash
cd /home/tuna/ADTools/LessDestructiveFarm-main
```

Docker run:
```bash
docker-compose up -d
```
---

## 3)🔥 firegex-main 🔥

### What it does
Firegex is a firewall/security toolset for Linux traffic control:
- backend API (Python/FastAPI-style layout),
- netfilter-based modules (`nfproxy`, `nfregex`, `porthijack`),
- frontend UI,
- CLI/library package under `fgex-lib/`,
- test and benchmark suite in `tests/`.

### How to run
From the project folder:

```bash
cd /home/tuna/ADTools/firegex-main
```

Python entrypoint:
```bash
python3 run.py
```

## 4)👩🏻‍💻 client-attacker (start_sploit) 👩🏻‍💻

### What it does
The attacker client launches your sploit on targets in a loop, extracts flags from sploit output,
and posts them to the farm API.

### How to run
From the project folder:

```bash
cd /home/tuna/ADTools/ADTools/client-attacker
```

Run with your sploit file:

```bash
python3 start_sploit.py ./your_sploit.py
```

Run against local LessDestructiveFarm (default is already `http://127.0.0.1:3000`):

```bash
python3 start_sploit.py ./your_sploit.py --server-url http://127.0.0.1:3000
```

Optional token (if auth is enabled on farm API):

```bash
python3 start_sploit.py ./your_sploit.py --token YOUR_TOKEN
```

Useful options:

- `--attack-period 120` reruns attacks every N seconds.
- `--pool-size 50` limits concurrent sploit instances.
- `--distribute K/N` splits targets across multiple runner instances.
- `--not-per-team` runs one sploit process without per-team target arguments.

note: ```exploits/test.py``` is available as a simple example sploit that generates fake flags for testing.
```
python3 start_sploit.py -u http://localhost:3000 exploits/test.py
```

(I think that since http://localhost:3000 is the default server URL, you can omit the `-u` option in this case, but it doesn't hurt to be explicit.)

---

## 5)🚩 test-flag-checker 🚩

### What it does
Standalone checker service used to test LessDestructiveFarm end-to-end without modifying farm source code.

- Receives submitted flags on `PUT /flags`
- Returns checker statuses (`RESUBMIT`, `ACCEPTED`, `DENIED`)
- Provides a manual review UI at `http://127.0.0.1:8080/ui`

### How to run

```bash
cd /home/tuna/ADTools/ADTools/test-flag-checker
npm install
npm start
```

### Notes (important)

- LessDestructiveFarm will not submit any flags if `TEAM_TOKEN` is empty.
- LDFarm container must point to checker host using Docker bridge gateway (example `172.18.0.1`), not `127.0.0.1` from inside container.
- Decisions can look delayed: LDFarm submit loop is periodic (default around 120 seconds), so accept/deny is reflected on the next submit cycle.

### LDFarm env required for this checker

```bash
TEAM_TOKEN=test
FLAG_SUBMIT_URL=http://172.18.0.1:8080/flags
FLAG_IDS_BASE_URL=http://172.18.0.1:8080
```

Apply env by recreating app service:

```bash
cd /home/tuna/ADTools/ADTools/LessDestructiveFarm-main
docker compose up -d --force-recreate app
```

Quick check:

```bash
docker compose exec -T app env | grep -E 'TEAM_TOKEN|FLAG_SUBMIT_URL|FLAG_IDS_BASE_URL'
curl -s http://127.0.0.1:8080/api/flags
```

I tested the checker with the example sploit and it seems to be working fine, with flags appearing in the checker UI and LDFarm logs showing successful submissions (both accepted and denied flags are reflected correctly based on manual review in the UI).

---

## Requirements

Install these base tools on Linux:

- Docker + Docker Compose plugin
- Node.js + npm
- Python 3 + pip
- (For firewall/netfilter features) root privileges and compatible Linux kernel/network stack

---

## Notes

- Each project has its own `README.md` with detailed configuration and environment variables.
- Start with the per-project README before production use.
- Some tools interact with networking/firewall subsystems; run only in controlled environments.


## How to access to VPS

```bash
ssh root@49.13.233.25
```

git clone

```bash
git clone https://github.com/Maalissa3/ADTools.git

