# Tulip Overview

Tulip is an Attack/Defence CTF flow analyzer that helps teams inspect traffic and quickly recreate attacks from captured sessions.

This overview focuses on:
- What each major folder does
- How the system fits together
- What is still incomplete or not configured yet (based on README)

## 1) What Tulip Does

Tulip ingests network traffic (pcap and optionally Suricata alerts), enriches/parses it, stores it, and exposes it through a web UI where you can:
- Search/filter flows and tags
- Inspect decoded protocol details
- Diff flows
- Use correlation views (time/packets/volume)
- Copy generated Python snippets to replay attacks

## 2) High-Level Architecture

- Frontend: React + TypeScript + Vite app in `frontend/`
- API service: Python web service and data logic in `services/api/`
- Ingestion pipeline: Go-based assembler/enricher in `services/go-importer/`
- Database: Timescale/PostgreSQL with schema in `services/schema/`
- Optional features: Suricata synchronization, flag ID scraping/scanning, PCAP-over-IP

## 2.1) Ingestion Methods

Tulip can receive traffic in two practical ways:

| Feature | Method A: PCAP Files | Method B: Live Stream |
| --- | --- | --- |
| Reliability | Very high; files act as a buffer. | Medium; packets can drop if the network is saturated. |
| Latency | 30-60 seconds, depending on rotation and sync timing. | Near-instant. |
| Complexity | Lower; standard Linux tools are enough. | Higher; requires PCAP-over-IP setup. |
| Disk Usage | Higher; temporary PCAP storage is needed. | Lower; traffic is processed on the fly. |

README guidance points to PCAP files as the default, simpler path. Live streaming is available through PCAP-over-IP when you need lower latency and can tolerate the added setup.

## 2.2) Method A: Pipeline Setup

Method A is the normal file-based workflow for Tulip. The basic sequence is:

1. Capture traffic on the vulnbox with a rotating PCAP tool such as `tcpdump`.
2. Copy completed PCAP files to the Tulip host with `rsync`, `scp`, or a similar transfer.
3. Move files into the watched ingest directory only after transfer is complete.
4. Let the Go assembler/enricher pipeline pick them up automatically.
5. View the parsed flows in the web UI once they are stored.

Practical notes:

- Rotating files every minute is a good default for competition use because it keeps chunks manageable and gives Tulip a steady stream of complete files.
- Using a temporary staging directory on the Tulip host before moving files into the watched ingest directory avoids partially written reads.
- PCAP files are mandatory in this workflow, and they must be rotated or deleted regularly so the vulnbox does not run out of disk space.
- The current codebase stores processed flows in Timescale/PostgreSQL, not MongoDB.
- If you also run Suricata, Tulip can ingest its `eve.json` output alongside PCAP files.

### Capturing with `tcpdump`

On the vulnbox, use a rotating capture directory and write one file per interval:

```bash
mkdir /var/log/tcpdump
mkdir /var/log/tcpdump/3000
chmod -R 777 /var/log/tcpdump
'tcpdump -i game (port 3000 or port 5000...) -G 120 -w /var/log/tcpdump/3000/dump-3000-%H\:%M\:%S.pcap'
```

If you want to limit capture size instead of time, `tcpdump` also supports rotation by file size with `-C`.

### Transferring with `rsync`

After a PCAP finishes writing, copy it to the Tulip host. A simple approach is:

```bash
rsync -avz /tmp/capture/ user@tulip-host:/tmp/tulip-inbox/
mv /tmp/tulip-inbox/*.pcap /path/to/watched/ingest/
```

*Personally, I run ./pluto.sh that's in `/home/tuna/ADTools/ADTools/tulip-master/services/pcaps/pluto.sh`*

The key idea is to copy into a staging folder first, then move the completed file into the watched ingest directory so Tulip only sees finished PCAPs.

If you prefer a loop, you can repeatedly sync new files and only move them into the watched folder after the transfer succeeds.

## 3) Repository Map

### Root and deployment

- `README.md`: Main setup, usage, Suricata integration, and security notes.
- `OVERVIEW.md`: High-level project map and setup status.
- `SECURITY.md`: Security policy and instructions.
- `docker-compose.yml`: Primary deployment stack.
- `docker-compose-test.yml`: Test stack with test flagid endpoint.
- `docker-compose-suricata.yml`: Suricata-enabled stack variant.
- `start.sh`, `dev.sh`, `test.sh`: Convenience scripts for run/dev/test workflows.
- `.env.example`: Environment variable template.
- `.devcontainer/`, `.vscode/`, `.github/`: Editor, dev container, and CI metadata.

### Frontend

- `frontend/`: React + TypeScript + Vite UI.
- `frontend/src/pages/`: Main pages such as home, flow view, and diff view.
- `frontend/src/components/`: Reusable UI components.
- `frontend/src/store/`: Client-side state and filter logic.
- `frontend/src/api.ts`: Frontend API client wrapper.
- `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/vite.config.ts`: Styling and build tooling.

### Backend API

- `services/api/`: Python API and flow-processing backend.
- `services/api/webservice.py`: Web entrypoint.
- `services/api/database.py`: Database access layer.
- `services/api/configurations.py`: Service/game target configuration.
- `services/api/flow2pwn.py`, `services/api/data2req.py`, `services/api/json_util.py`: Utility and transform modules.

### Ingestion and enrichment

- `services/go-importer/`: Go-based traffic ingestion pipeline.
- `services/go-importer/cmd/assembler/`: Assembles traffic into Tulip flows.
- `services/go-importer/cmd/enricher/`: Enrichment stage.
- `services/go-importer/converters/`: Protocol/data decoders and helper scripts.
- `services/go-importer/internal/pkg/db/`: DB batching and writes.
- `services/go-importer/test_data/`: Sample traffic and generators.

### Database and schema

- `services/schema/`: SQL schema and DB-side functions/statistics.
- `services/schema/schema.sql`
- `services/schema/functions.sql`
- `services/schema/statistics.sql`
- `services/schema/system.sql`

### Optional services

- `services/flagids/`: Flag ID helper service.
- `services/timescale/`: Timescale/PostgreSQL service build context.
- `services/timescale/tulip/`: Custom extension source tree.

### Sample and shared data

- `services/test_pcap/`: Sample pcap/eve/rule files.
- `demo_images/`: Screenshots used in the README.
- `shared/`: Shared mount placeholder (`.gitkeep`).

### Runtime flow

1. Configure `.env` from `.env.example`.
2. Configure service targets in `services/api/configurations.py`.
3. Start the stack with Docker Compose.
4. Ingestor watches traffic directories for new PCAP files and optional Suricata logs.
5. Parsed/enriched data lands in Timescale/PostgreSQL.
6. Frontend queries the API and renders searchable/diffable flow views.

## 5) What Is Missing / Incomplete (From README)

These are the main items that are not complete out of the box and must be configured or intentionally enabled.

## Required before real use

- Missing environment setup:
  - You still need to create `.env` (`cp .env.example .env`) and fill real values.
- Missing target/service configuration:
  - You still need to edit `services/api/configurations.py` with your real vulnbox/service IPs and ports.

## 6) Suggested Completion Checklist

- [ ] Create and tune `.env` for your environment.
- [ ] Update `services/api/configurations.py` with real targets.
- [ ] Confirm traffic ingestion path and bind mounts (`TRAFFIC_DIR_HOST`).
- [ ] Bring up core stack and verify frontend/API/DB health.
- [ ] Decide whether to enable: experimental cookie linking, PCAP-over-IP, flag ID scraping/scanning.
- [ ] If enabling Suricata sync, configure and run `docker-compose-suricata.yml`.
- [ ] Add access control or isolate deployment network before competition use.


## 7)Checklist

##  Live A/D Competition Mode

- [ ] Update `.env` and set real values.
- [ ] Update `services/api/configurations.py` with real service IP/port definitions.
- [ ] Start rotating capture on vulnboxes and sync captures to the Tulip host.
- [ ] Run the main stack (`docker-compose.yml`) and verify frontend + API are reachable.
- [ ] Keep Tulip on internal network or behind VPN/authentication.
- [ ] Enable only needed optional features to reduce operational risk during game time.


## Command safety notes:

- Always use the same env/file context for lifecycle commands:
  - `docker compose --env-file .env.test -f docker-compose-test.yml up -d --build`
  - `docker compose --env-file .env.test -f docker-compose-test.yml down -v`
- Running `docker compose down -v` without `--env-file` and `-f` can fail with invalid empty volume specs (missing substituted variables).
