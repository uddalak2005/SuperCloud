import os
import json
import re
from typing import Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from groq import AsyncGroq
from agents.base_agent import BaseAgent

load_dotenv()


class RCABrainAgent(BaseAgent):

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "rca_brain")

        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = AsyncGroq(api_key=self.groq_api_key)

    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:

        incident_id = telemetry_payload.get("incident_id", "unknown")
        severity = telemetry_payload.get("severity", "low")
        anomaly_score = telemetry_payload.get("anomaly_score", 0.0)

        context = self.build_investigation_context(telemetry_payload)

        rca_result = await self.perform_llm_reasoning(
            context,
            incident_id,
            severity,
            anomaly_score
        )

        return {
            "action": "rca_complete",
            "parameters": rca_result
        }

    def build_investigation_context(self, telemetry_payload: Dict[str, Any]) -> str:

        metrics = telemetry_payload.get("metrics", {})
        logs = telemetry_payload.get("logs", {})

        if isinstance(logs, dict):
            logs = [logs]

        return f"""
You are analyzing a production incident.

METRICS:
{json.dumps(metrics, indent=2)}

LOGS:
{json.dumps(logs, indent=2)}

Classify:
- issue_type
- severity
- execution environment (kubernetes | docker | systemd | host)
"""

    async def perform_llm_reasoning(
        self,
        context: str,
        incident_id: str,
        severity: str,
        anomaly_score: float
    ) -> Dict:

        prompt = f"""
            You are an AI Root Cause Classification Engine.

            {context}

            Return ONLY raw JSON.
            No explanations.
            No markdown.
            Must start with '{{' and end with '}}'.

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
            matches = re.findall(r"\{[\s\S]*\}", content)

            if not matches:
                raise ValueError("No JSON object found")

            parsed = json.loads(matches[-1])

            return parsed

        except Exception as e:
            print("RCA PARSE ERROR:", str(e))

            return {
                "version": "2.0",
                "incident_id": incident_id,
                "issue_type": "",
                "confidence": 0.0,
                "severity": severity,
                "target": {
                    "environment": "",
                    "deployment_name": "",
                    "pod_name": "",
                    "container_name": "",
                    "service_name": "",
                    "namespace": ""
                },
                "strategy_override": {
                    "replica_count": "",
                    "force_restart": "",
                    "skip_canary": False
                },
                "metadata": {
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "anomaly_score": anomaly_score,
                    "trigger_metric": {}
                }
            }
