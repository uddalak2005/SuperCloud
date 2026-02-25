import os
import json
import re
from typing import Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from groq import AsyncGroq
from agents.base_agent import BaseAgent

load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))
rulebook_path = os.path.join(base_dir, "rulebook.json")


class RCABrainAgent(BaseAgent):

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "rca_brain")

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = AsyncGroq(api_key=self.groq_api_key)

        with open(rulebook_path) as f:
            self.rulebook = json.load(f)

        self.valid_issue_types = list(self.rulebook["issues"].keys())

    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:

        incident_id = telemetry_payload.get("incident_id", "unknown")
        severity = telemetry_payload.get("severity", "low")
        anomaly_score = telemetry_payload.get("anomaly_score", 0.0)

        context = self.build_investigation_context(telemetry_payload)

        rca_result = await self.perform_llm_reasoning(
            context,
            incident_id,
            severity,
            anomaly_score,
            telemetry_payload
        )

        if rca_result.get("action") == "alert_only":
            return rca_result

        return {
            "action": "rca_complete",
            "parameters": rca_result
        }

    def build_investigation_context(self, telemetry_payload: Dict[str, Any]) -> str:

        metrics = telemetry_payload.get("metrics", {})
        logs = telemetry_payload.get("logs", {})
        anomaly_type = telemetry_payload.get("anomaly_type", "unknown")

        if isinstance(logs, dict):
            logs = [logs]

        valid_issues = "\n".join(
            [f"- {i}" for i in self.valid_issue_types]
        )

        return f"""
You are analyzing a production incident.

ANOMALY TYPE:
{anomaly_type}

METRICS:
{json.dumps(metrics, indent=2)}

LOGS:
{json.dumps(logs, indent=2)}

Valid issue_type options:
{valid_issues}

Choose ONLY from the above.
If none apply return:
"issue_type": "none"
"confidence": 0.0

Classify:
- issue_type
- severity
- execution environment (kubernetes | docker | systemd | host)

Return ONLY valid JSON.
"""

    def validate_llm_output(self, parsed: Dict[str, Any]) -> Dict[str, Any] | None:

        issue_type = parsed.get("issue_type")

        if issue_type == "none":
            return {
                "action": "alert_only",
                "reason": "no_matching_rule"
            }

        if issue_type not in self.valid_issue_types:
            print("Invalid issue_type:", issue_type)
            return None

        # Validate environment (RELAXED)
        actual_env = parsed.get("target", {}).get("environment", "")
        if not actual_env:
            print("Missing environment")
            return None

        actual_env = actual_env.strip().lower()
        parsed["target"]["environment"] = actual_env

        allowed_envs = ["docker", "kubernetes", "systemd", "host"]
        if actual_env not in allowed_envs:
            print("Invalid environment:", actual_env)
            return None

        # Confidence relaxed
        if parsed.get("confidence", 0) < 0.4:
            return {
                "action": "alert_only",
                "reason": "low_confidence"
            }

        return parsed

    def enrich_target_fields(self, parsed: Dict[str, Any], telemetry_payload: Dict[str, Any]):

        target = parsed.get("target", {})
        env = target.get("environment")

        logs = telemetry_payload.get("logs", {})
        service_name = logs.get("service", "")
        host = telemetry_payload.get("host", "")

        if env == "docker":
            target["container_name"] = service_name or host

        elif env == "kubernetes":
            target["deployment_name"] = service_name
            target["namespace"] = "default"

        elif env == "systemd":
            target["service_name"] = service_name

        elif env == "host":
            target["service_name"] = service_name

        parsed["target"] = target
        return parsed

    async def perform_llm_reasoning(
        self,
        context: str,
        incident_id: str,
        severity: str,
        anomaly_score: float,
        telemetry_payload: Dict[str, Any]
    ) -> Dict:

        prompt = f"""
You are an AI Root Cause Classification Engine.

{context}

Required schema:

{{
  "version": "2.0",
  "incident_id": "{incident_id}",
  "issue_type": "string",
  "confidence": 0.0,
  "severity": "{severity}",
  "target": {{
      "environment": "kubernetes | docker | systemd | host",
      "deployment_name": "",
      "pod_name": "",
      "container_name": "",
      "service_name": "",
      "namespace": ""
  }},
  "strategy_override": {{
      "replica_count": "",
      "force_restart": "",
      "skip_canary": false
  }},
  "metadata": {{
      "detected_at": "{datetime.now(timezone.utc).isoformat()}",
      "anomaly_score": {anomaly_score},
      "trigger_metric": {{}}
  }}
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=1024,
                top_p=0.9,
                stream=False
            )

            content = response.choices[0].message.content.strip()
            cleaned = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("No JSON found")

            parsed = json.loads(cleaned[start:end+1])

            validated = self.validate_llm_output(parsed)

            if not validated:
                return {
                    "action": "alert_only",
                    "reason": "validation_failed"
                }

            enriched = self.enrich_target_fields(validated, telemetry_payload)

            return enriched

        except Exception as e:
            print("RCA ERROR:", str(e))
            return {
                "action": "alert_only",
                "reason": "rca_parse_failed"
            }