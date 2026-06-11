# Wazuh SOC Detection Lab

A hands-on security operations lab built on Wazuh 4.14.5, simulating real-world threat detection using the Cyber Kill Chain and MITRE ATT&CK framework. This project demonstrates SOC analyst workflows — from attack simulation to alert triage and detection gap analysis.

---

## What This Project Does

This lab deploys a full open-source SIEM stack and monitors a dedicated attack target VM. Real attacks are simulated using Atomic Red Team across all seven stages of the Cyber Kill Chain, generating authentic security alerts triaged directly in the Wazuh dashboard. Detection gaps in Wazuh's default ruleset are documented with remediation recommendations.

```
Attack simulation (Atomic Red Team — 7-stage Kill Chain)
        ↓
WazuhTarget VM (Ubuntu 22.04 — monitored endpoint)
        ↓
Wazuh 4.14.5 (SIEM — detects threats, fires alerts)
        ↓
Wazuh Dashboard (alert triage and investigation)
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
```

---

## Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| SIEM | Wazuh 4.14.5 | Threat detection, 6775+ rules |
| Container | Docker Compose | Single-node Wazuh stack |
| Attack simulation | Atomic Red Team | MITRE ATT&CK technique simulation |
| Target VM | Ubuntu 22.04 (VirtualBox) | Monitored endpoint |

---

## Cyber Kill Chain Detection Lab

A full 7-stage attack was simulated against the WazuhTarget VM and detection results were captured from the Wazuh manager. See [docs/kill_chain_detection_lab.md](docs/kill_chain_detection_lab.md) for the complete writeup.

### Detection Results

| Stage | Technique | MITRE ID | Detected | Rule IDs |
|---|---|---|---|---|
| 1 Reconnaissance | System Info + Port Scan | T1082, T1046 | ❌ Gap | — |
| 2 Weaponization | Obtain Capabilities | T1588 | N/A | — |
| 3 Delivery | Brute Force: Password Guessing | T1110.001 | ✅ | 5503, 5401 |
| 4 Exploitation | Valid Accounts | T1078 | ✅ | 5402, 5501 |
| 5 Installation | Create Account + Cron | T1136.001, T1053.003 | ✅ | 5901, 5902, 2833 |
| 6 C2 | Unix Shell Execution | T1059.004 | ❌ Gap | — |
| 7 Actions on Objectives | Clear History + Collection | T1070.003, T1005 | ❌ Gap | — |

**Detection rate:** 3 of 7 stages detected using Wazuh default rules (43%)

### Key Findings

Wazuh's default ruleset provides strong coverage at the authentication layer — brute force patterns, credential success following failures, and high-severity persistence events (account creation, crontab modification) are clearly visible and form a coherent attack narrative.

Detection gaps exist at the process execution and network layers. Host-based recon using built-in tools, outbound C2 traffic, file access without modification, and log tampering are not covered by default rules. These gaps require auditd integration, Suricata, or custom rule development.

---

## MITRE ATT&CK Coverage

| Technique | Name | Tactic | Status |
|---|---|---|---|
| T1082 | System Information Discovery | Discovery | ❌ Gap |
| T1046 | Network Service Discovery | Discovery | ❌ Gap |
| T1110.001 | Brute Force: Password Guessing | Credential Access | ✅ Detected |
| T1078 | Valid Accounts | Initial Access / Privilege Escalation | ✅ Detected |
| T1136.001 | Create Local Account | Persistence | ✅ Detected |
| T1053.003 | Scheduled Task: Cron | Persistence | ✅ Detected |
| T1059.004 | Unix Shell | Command and Control | ❌ Gap |
| T1070.003 | Clear Command History | Defense Evasion | ❌ Gap |
| T1005 | Data from Local System | Collection | ❌ Gap |

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
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

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env with your chosen passwords
```

### 4. Generate SSL certificates

```bash
docker compose -f generate-indexer-certs.yml run --rm generator
```

### 5. Start Wazuh

```bash
docker compose up -d
```

Wait 3 minutes for the manager to fully boot.

---

## Credentials

| Service | URL | Default username |
|---|---|---|
| Wazuh Dashboard | https://localhost | admin |
| Wazuh API | https://localhost:55000 | wazuh-wui |

Passwords are set via `.env` — see `.env.example` for required variables.

> ⚠️ Change default credentials before any production use.

---

## Project Structure

```
wazuh-soc-lab/
├── config/                          # Wazuh stack configuration
├── docs/
│   └── kill_chain_detection_lab.md  # Full kill chain writeup
├── docker-compose.yml               # Wazuh 4.14.5 single-node stack
├── generate-indexer-certs.yml       # SSL certificate generation
├── .env.example                     # Credential template
└── README.md
```

---

## What I Learned

- Deploying and configuring an enterprise-grade SIEM in Docker
- How Wazuh's detection pipeline works — agents → manager → indexer
- Simulating MITRE ATT&CK techniques using Atomic Red Team across all 7 kill chain stages
- SOC analyst triage workflows — triaging real security alerts from live simulations
- Identifying and documenting SIEM detection gaps with remediation recommendations
- Debugging agent configuration issues (ossec.conf localfile, PAM log ingestion)

---

## Future Enhancements

The core lab is complete and fully functional. The following extensions would deepen detection coverage and are identified directly from the gap analysis performed during the kill chain simulation.

- **Custom Wazuh rules** — frequency-based brute force correlation for T1110.001 (N failures within a time window triggering a level 10 alert), and a dedicated rule for `.bash_history` deletion (T1070.003)
- **auditd integration** — ingesting `/var/log/audit/audit.log` would close the three largest detection gaps: host recon (T1082), port scanning (T1046), and shell execution (T1059.004)
- **Suricata IDS** — network-layer visibility for outbound C2 traffic (T1071) and internal scanning that auth.log never captures
- **Sigma rules** — translating confirmed detections into portable Sigma format for cross-SIEM compatibility and public contribution
- **MITRE ATT&CK Navigator heatmap** — visualising detection coverage across all 9 simulated techniques in a single view

---

## References

- [Wazuh Documentation](https://documentation.wazuh.com)
- [MITRE ATT&CK Framework](https://attack.mitre.org)
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
- [Cyber Kill Chain — Lockheed Martin](https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html)
- [Wazuh Docker Deployment](https://documentation.wazuh.com/current/deployment-options/docker/wazuh-container.html)

---