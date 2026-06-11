import httpx
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from app.modules.store import insert_alert

load_dotenv()

WAZUH_HOST       = os.getenv("WAZUH_HOST", "https://localhost:55000")
INDEXER_URL      = os.getenv("WAZUH_INDEXER_URL", "https://localhost:9200")
INDEXER_USER     = os.getenv("WAZUH_INDEXER_USER", "admin")
INDEXER_PASSWORD = os.getenv("WAZUH_INDEXER_PASSWORD", "")
VERIFY_SSL       = os.getenv("WAZUH_VERIFY_SSL", "false").lower() == "true"

def normalise(hit: dict) -> dict:
    agent  = hit.get("agent", {})
    rule   = hit.get("rule", {})
    groups = rule.get("groups", [])
    return {
        "id":               hit.get("id", ""),
        "timestamp":        hit.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "agent_name":       agent.get("name", "unknown"),
        "agent_ip":         agent.get("ip", "unknown"),
        "rule_id":          str(rule.get("id", "")),
        "rule_description": rule.get("description", ""),
        "rule_level":       int(rule.get("level", 0)),
        "rule_groups":      ",".join(groups) if isinstance(groups, list) else str(groups),
        "location":         hit.get("location", ""),
        "full_log":         hit.get("full_log", "")
    }

async def fetch_alerts(limit: int = 500) -> int:
    async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
        response = await client.get(
            f"{INDEXER_URL}/wazuh-alerts-*/_search",
            auth=httpx.BasicAuth(INDEXER_USER, INDEXER_PASSWORD),
            params={"size": limit, "sort": "@timestamp:desc"},
            timeout=30.0
        )
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        count = 0
        for hit in hits:
            source = hit["_source"]
            source["id"] = hit["_id"]
            normalised_alert = normalise(source)
            insert_alert(normalised_alert)
            count += 1
        print(f"[ingestor] fetched and stored {count} alerts")
        return count