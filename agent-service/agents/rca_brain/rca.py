import os
import json
import re
from typing import Dict, Any
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

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
        CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

        with open(CONFIG_PATH, "r") as f:
            self.remediation_policy = json.load(f)

       
        


    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:

        investigation_context = self.build_investigation_context(
            telemetry_payload
        )

        rca_result = await self.perform_llm_reasoning(
            investigation_context
        )

        return {
            "action": "rca_complete",
            "parameters": {
                "root_cause": rca_result.get("root_cause"),
                "affected_services": rca_result.get("affected_services", []),
                "confidence": rca_result.get("confidence", 0.0),
                "fixes": rca_result.get("fixes", [])
            }
        }


    def build_investigation_context(self, telemetry_payload: Dict[str, Any]) -> str:

        metrics = telemetry_payload.get("metrics", {})
        logs = telemetry_payload.get("logs", [])

        if isinstance(logs, dict):
            logs = [logs]

        pretty_metrics = json.dumps(metrics, indent=2)
        pretty_logs = json.dumps(logs, indent=2)

        context = f"""
            You are analyzing a production incident.

            METRICS SNAPSHOT:
            {pretty_metrics}

            LOG EVENTS:
            {pretty_logs}

            If log level == ERROR, treat it as high priority.
            Correlate logs and metrics before concluding.
            """

        return context


    async def perform_llm_reasoning(self, context: str) -> Dict:

        rulebook_json = json.dumps(self.remediation_policy, indent=2)

        prompt = f"""
            You are a senior Site Reliability Engineer performing structured Root Cause Analysis (RCA)
            in a production cloud-native environment.

            {context}

            ==============================
            APPROVED REMEDIATION POLICY
            ==============================
            You MUST strictly follow the remediation policy below.
            You are NOT allowed to invent commands.
            You are NOT allowed to modify command templates.
            You may ONLY choose from the issues and steps defined.

            {rulebook_json}

            ==============================
            INSTRUCTIONS
            ==============================

            1. Identify the most probable root cause.
            2. Identify affected services.
            3. Select the correct issue category from the policy.
            4. Select remediation steps in priority order.
            5. Include rollback command from the selected issue.
            6. If health_check is defined, include it.
            7. If canary_strategy is enabled, mention canary execution.
            8. Respect global policy (circuit breaker, retry limits).
            9. Provide confidence score between 0 and 1.

            CRITICAL OUTPUT RULES:
            - Return ONLY raw JSON.
            - No explanations.
            - No reasoning.
            - No markdown.
            - No <think> blocks.
            - Must start with '{{' and end with '}}'.

            Required JSON schema:

            {{
                "root_cause": "...",
                "affected_services": ["..."],
                "confidence": 0.0,
                "selected_issue": "...",
                "canary_required": true/false,
                "health_check": {{
                    "type": "...",
                    "command": "..."
                }},
            "fixes": [
            {{
                "description": "...",
                "command": "...",
                "priority": 1
            }}
            ],
            "rollback": {{
                "description": "...",
                "command": "..."
            }}
        }}
        """

        try:
            response = await self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_completion_tokens=2048,
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
                "root_cause": "Invalid LLM JSON response",
                "affected_services": [],
                "confidence": 0.0,
                "selected_issue": None,
                "canary_required": False,
                "health_check": None,
                "fixes": [],
                "rollback": None
            }
