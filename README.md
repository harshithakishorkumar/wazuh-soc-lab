# Wazuh SOC Detection Lab

A hands-on security operations lab built on Wazuh 4.14.5, simulating real-world threat detection using MITRE ATT&CK techniques. This project demonstrates end-to-end SOC analyst workflows — from attack simulation to alert triage.

---

## What This Project Does

This lab deploys a full open-source SIEM stack and monitors a dedicated attack target VM. Real attacks are simulated using Atomic Red Team, generating authentic security alerts that flow through a custom Python enrichment pipeline. Detection gaps in Wazuh's default ruleset are filled with custom rules mapped to MITRE ATT&CK.

```
Attack simulation (Atomic Red Team)
        ↓
WazuhTarget VM (Ubuntu 22.04 — monitored endpoint)
        ↓
Wazuh 4.14.5 (SIEM — detects threats, fires alerts)
        ↓
Python pipeline (ingests and enriches alerts every 5 minutes)
        ↓
DuckDB (stores alerts with MITRE tagging and triage status)
        ↓
FastAPI (serves enriched alerts via REST API)
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Docker (WSL Ubuntu)                        │
│  ├── wazuh.manager  :55000  (detection)     │
│  ├── wazuh.indexer  :9200   (storage)       │
│  └── wazuh.dashboard :443   (web UI)        │
└─────────────────────────────────────────────┘
        ↑ agent events
┌─────────────────────────────────────────────┐
│  WazuhTarget VM (VirtualBox Ubuntu 22.04)   │
│  ├── Wazuh agent 4.14.5                     │
│  ├── PowerShell 7.x                         │
│  └── Atomic Red Team                        │
└─────────────────────────────────────────────┘
        ↑ alert ingestion
┌─────────────────────────────────────────────┐
│  Python App                                 │
│  ├── ingestor.py   (polls OpenSearch)       │
│  ├── store.py      (DuckDB read/write)      │
│  └── main.py       (FastAPI :8000)          │
└─────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| SIEM | Wazuh 4.14.5 | Threat detection, 6775+ rules |
| Container | Docker Compose | Single-node Wazuh stack |
| Attack simulation | Atomic Red Team | MITRE ATT&CK technique simulation |
| Backend | FastAPI + Python | Alert ingestion and enrichment API |
| Database | DuckDB | Embedded alert storage with triage status |
| Network polling | httpx + APScheduler | Async alert polling every 5 min |

---

## MITRE ATT&CK Coverage

Techniques simulated and validated:

| Technique | Name | Tactic | Status |
|---|---|---|---|
| T1110.001 | Brute Force: SUDO | Credential Access | ✅ Detected |
| T1087.001 | Account Discovery | Discovery | ✅ Detected |

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.10+
- VirtualBox (for WazuhTarget VM)
- WSL2 Ubuntu (for running the stack)

### 1. Clone the repo

```bash
git clone git@github.com:harshithakishorkumar/wazuh-soc-lab.git
cd wazuh-soc-lab
```

### 2. Set kernel memory limit

```bash
sudo sysctl -w vm.max_map_count=262144
```

### 3. Generate SSL certificates

```bash
docker compose -f generate-indexer-certs.yml run --rm generator
```

### 4. Start Wazuh

```bash
docker compose up -d
```

Wait 3 minutes for the manager to fully boot.

### 5. Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Wazuh credentials
```

### 6. Start the pipeline

```bash
uvicorn app.main:app --reload
```

---

## Credentials

| Service | URL | Username | Password |
|---|---|---|---|
| Wazuh Dashboard | https://localhost | admin | SecretPassword |
| Wazuh API | https://localhost:55000 | wazuh-wui | see .env |
| FastAPI docs | http://localhost:8000/docs | — | — |

> ⚠️ Change default credentials before any production use.

---

## Project Structure

```
wazuh-soc-lab/
├── app/
│   ├── main.py              # FastAPI entry point + scheduler
│   └── modules/
│       ├── ingestor.py      # Polls Wazuh OpenSearch indexer
│       └── store.py         # DuckDB read/write layer
├── config/                  # Wazuh stack configuration
├── data/                    # DuckDB alert database
├── docs/                    # Setup guides and references
├── docker-compose.yml       # Wazuh 4.14.5 single-node stack
└── requirements.txt
```


---

## What I Learned

- Deploying and configuring an enterprise-grade SIEM in Docker
- How Wazuh's detection pipeline works — agents → manager → indexer
- Writing Python async pipelines with FastAPI and APScheduler
- Simulating MITRE ATT&CK techniques using Atomic Red Team
- SOC analyst triage workflows — triaging real security alerts
- OpenSearch query patterns for security data retrieval

---

## Roadmap

- [x] Deploy Wazuh 4.14.5 single-node stack
- [x] Connect WazuhTarget VM as monitored endpoint
- [x] Build Python alert ingestion pipeline
- [x] Simulate T1110.001 and T1087.001 with Atomic Red Team
- [ ] Write custom Wazuh detection rules mapped to MITRE ATT&CK
- [ ] Suricata network IDS integration
- [ ] MITRE ATT&CK coverage gap analysis
- [ ] Sigma rule translations

---

## References

- [Wazuh Documentation](https://documentation.wazuh.com)
- [MITRE ATT&CK Framework](https://attack.mitre.org)
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
- [Wazuh Docker Deployment](https://documentation.wazuh.com/current/deployment-options/docker/wazuh-container.html)

---
