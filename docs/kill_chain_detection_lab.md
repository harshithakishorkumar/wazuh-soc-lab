# Cyber Kill Chain Detection Lab — Wazuh SOC Lab

## Overview

This lab demonstrates end-to-end detection of a multi-stage attack using the Lockheed Martin Cyber Kill Chain framework. Each stage was simulated using Atomic Red Team on a live Ubuntu 22.04 target with a Wazuh 4.14.5 agent, and detection results were captured from the Wazuh manager.

**Environment:**
- Wazuh Manager: 4.14.5 (Docker on WSL Ubuntu)
- Target Agent: Ubuntu 22.04 LTS (VirtualBox VM, agent ID 003, hostname: wazuhtarget)
- Simulation Framework: Atomic Red Team (PowerShell)
- Alert Storage: DuckDB via custom FastAPI ingestion pipeline

---

## Attack Scenario

An external threat actor with initial network access attempts to move laterally to a Linux server running SSH on port 22. The attacker enumerates the system, brute forces credentials, establishes persistence, and attempts to cover their tracks.

---

## Kill Chain Stages

### Stage 1 — Reconnaissance
**MITRE:** T1082 (System Information Discovery), T1046 (Network Service Discovery)
**Tactic:** TA0007 Discovery
**Timestamp:** 2026-06-11 11:16 UTC

**What the attacker did:**
Ran built-in Linux commands to fingerprint the target OS and scan local ports. Discovered Ubuntu 22.04.5 LTS, kernel 5.15.0, VirtualBox/KVM hypervisor, and confirmed only port 22 (SSH) is open.

**Simulation:**
```
Invoke-AtomicTest T1082 -TestNumbers 3,4
for port in 22 80 443 3306 ...; do (echo >/dev/tcp/127.0.0.1/$port) 2>/dev/null && echo "port $port is open"; done
```

**Wazuh Detection:** Not detected
**Detection Gap:** Wazuh's default ruleset has no rule matching passive enumeration via built-in commands (uname, lscpu, DMI reads). These commands generate no auth.log entries and are indistinguishable from legitimate admin activity without auditd or process execution monitoring.

**Recommendation:** Enable auditd with rules watching for rapid sequential enumeration commands by non-root users. Alternatively configure Wazuh's `<localfile>` to ingest `/var/log/audit/audit.log`.

---

### Stage 2 — Weaponization
**MITRE:** T1588 (Obtain Capabilities)
**Tactic:** TA0042 Resource Development
**Timestamp:** Not observable

**What the attacker did:**
Based on recon findings (Ubuntu 22.04, SSH on port 22, sudo enabled), the attacker prepared a credential brute force script targeting the sudo PAM authentication service using a common password list.

**Wazuh Detection:** Not applicable — weaponization occurs off-target and is never directly observable in logs.

---

### Stage 3 — Delivery
**MITRE:** T1110.001 (Brute Force: Password Guessing)
**Tactic:** TA0006 Credential Access
**Timestamp:** 2026-06-11 11:18:38 UTC

**What the attacker did:**
Ran a brute force script against the sudo PAM service targeting the `art` account. Cycled through a password list — three wrong attempts followed by a successful match (`password123`) in under 12 seconds.

**Simulation:**
```
Invoke-AtomicTest T1110.001 -TestNumbers 5
```

**Wazuh Detection:** Detected ✅
| Rule ID | Level | Description | Count |
|---|---|---|---|
| 5503 | 5 | PAM: User login failed | 6 |
| 5401 | 5 | Failed attempt to run sudo | 6 |

**Evidence:** Rapid cluster of 5503 and 5401 alerts between 11:18:38 and 11:18:50 UTC — 12 failures in 12 seconds from user `art`.

---

### Stage 4 — Exploitation
**MITRE:** T1078 (Valid Accounts)
**Tactic:** TA0001 Initial Access, TA0004 Privilege Escalation
**Timestamp:** 2026-06-11 11:18:50 UTC

**What the attacker did:**
Password brute force succeeded. The attacker now has valid credentials for the `art` account with sudo access to root, effectively gaining full control of the target system.

**Wazuh Detection:** Detected ✅
| Rule ID | Level | Description |
|---|---|---|
| 5402 | 3 | Successful sudo to ROOT executed |
| 5501 | 3 | PAM: Login session opened |

**Evidence:** Rule 5402 fired immediately at 11:18:50 UTC — within the same second as the last brute force attempt, confirming credential success following the delivery stage.

---

### Stage 5 — Installation
**MITRE:** T1136.001 (Create Local Account), T1053.003 (Scheduled Task: Cron)
**Tactic:** TA0003 Persistence
**Timestamp:** 2026-06-11 11:18:37 UTC (user creation), 11:19:53 UTC (cron)

**What the attacker did:**
Created two backdoor accounts (`art`, `evil_user`) and modified root's crontab to establish persistent access. Even if the compromised account password is changed, access is maintained via the backdoor accounts and scheduled task.

**Simulation:**
```
Invoke-AtomicTest T1136.001 -TestNumbers 1
Invoke-AtomicTest T1053.003 -TestNumbers 1
```

**Wazuh Detection:** Detected ✅
| Rule ID | Level | Description | Count |
|---|---|---|---|
| 5901 | 8 | New group added to the system | 2 |
| 5902 | 8 | New user added to the system | 4 |
| 2833 | 8 | Root's crontab entry changed | 1 |

**Evidence:** High-severity (level 8) alerts for account creation and crontab modification within 90 seconds of exploitation — consistent with attacker establishing persistence immediately after gaining access.

---

### Stage 6 — Command and Control
**MITRE:** T1059.004 (Command and Scripting Interpreter: Unix Shell)
**Tactic:** TA0011 Command and Control
**Timestamp:** 2026-06-11 ~11:20 UTC

**What the attacker did:**
Executed a bash script that pinged an external IP (8.8.8.8), simulating outbound C2 communication to confirm internet connectivity from the compromised host.

**Simulation:**
```
Invoke-AtomicTest T1059.004 -TestNumbers 1
```

**Wazuh Detection:** Not detected
**Detection Gap:** Wazuh's default ruleset does not monitor outbound network connections or ICMP traffic. The bash script execution and ping to 8.8.8.8 generated no auth.log entries.

**Recommendation:** Enable network traffic monitoring via Suricata integration with Wazuh, or configure auditd to log process execution. Custom Sigma rules can detect unusual outbound connections from server-class systems.

---

### Stage 7 — Actions on Objectives
**MITRE:** T1070.003 (Indicator Removal: Clear Command History)
**Tactic:** TA0005 Defense Evasion, TA0009 Collection
**Timestamp:** 2026-06-11 ~11:21 UTC

**What the attacker did:**
Collected sensitive files (`/etc/passwd`, `/etc/shadow`, configuration files) and deleted bash history to cover tracks before disconnecting.

**Simulation:**
```
find /etc -name "*.conf" | head -10
cat /etc/passwd && cat /etc/shadow
Invoke-AtomicTest T1070.003 -TestNumbers 1
```

**Wazuh Detection:** Not detected
**Detection Gap:** File access without modification does not trigger Wazuh's File Integrity Monitoring (FIM). History file deletion is not monitored by default rules.

**Recommendation:** Configure Wazuh FIM to monitor `/etc/passwd`, `/etc/shadow`, and `/root/` with real-time monitoring enabled. Add a custom rule to alert on `.bash_history` deletion.

---

## Detection Summary

| Stage | Technique | MITRE ID | Detected | Rule IDs |
|---|---|---|---|---|
| 1 Reconnaissance | System Info + Port Scan | T1082, T1046 | ❌ Gap | — |
| 2 Weaponization | Obtain Capabilities | T1588 | N/A | — |
| 3 Delivery | Brute Force Password | T1110.001 | ✅ | 5503, 5401 |
| 4 Exploitation | Valid Accounts | T1078 | ✅ | 5402, 5501 |
| 5 Installation | Create Account + Cron | T1136.001, T1053.003 | ✅ | 5901, 5902, 2833 |
| 6 C2 | Unix Shell Execution | T1059.004 | ❌ Gap | — |
| 7 Actions | Clear History + Collection | T1070.003, T1005 | ❌ Gap | — |

**Detection rate:** 3 of 7 stages detected using Wazuh default rules (43%)

---

## Key Findings

**What Wazuh detected well:** Authentication-based attacks. The brute force pattern (repeated 5503/5401 followed by 5402) and high-severity persistence events (5902, 2833) are clearly visible in the alert timeline and provide a coherent attack narrative.

**What Wazuh missed:** Host-based recon using built-in tools, outbound C2 traffic, file access without modification, and log tampering. These are fundamental gaps in the default ruleset that require additional configuration.

**Detection gap pattern:** Wazuh's default coverage is strongest at the authentication layer (PAM/sudo) and weakest at the process execution and network layers. This is expected for a SIEM without auditd or an EDR agent.

---

## Recommended Improvements

1. **Enable auditd** and configure Wazuh to ingest `/var/log/audit/audit.log` — covers recon, C2, and file access gaps
2. **Custom FIM rules** for `/etc/passwd`, `/etc/shadow`, `.bash_history` with real-time monitoring
3. **Suricata integration** for network-based C2 detection
4. **Custom Sigma rules** for brute force correlation (frequency threshold on 5503 within a time window)

---

## Lab Note

Stages were simulated independently to verify individual detection capability. In a real incident the kill chain would follow chronological order. Alert timestamps reflect simulation order, not a live attack timeline. All simulations were conducted in an isolated lab environment on a dedicated virtual machine.