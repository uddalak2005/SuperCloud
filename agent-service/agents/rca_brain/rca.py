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
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.client = AsyncGroq(api_key=self.groq_api_key)


    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:
        investigation_context = self.build_investigation_context(telemetry_payload)
        rca_result = await self.perform_llm_reasoning(investigation_context)

        return {
            "action": "rca_complete",
            "parameters": {
                "root_cause": rca_result.get("root_cause"),
                "affected_services": rca_result.get("affected_services", []),
                "confidence": rca_result.get("confidence", 0.0),
                "recommended_fixes": rca_result.get("fixes", [])
            }
        }


    def build_investigation_context(self, telemetry_payload: Dict[str, Any]) -> str:
        try:
            pretty_telemetry_payload = json.dumps(
                telemetry_payload, indent=2, default=str
            )
        except Exception:
            pretty_telemetry_payload = str(telemetry_payload)

        context = f"""
            You are provided with an incident detected by an automated monitoring system.

            INCIDENT STATE:
            {pretty_telemetry_payload}
            """
        return context


    async def perform_llm_reasoning(self, context: str) -> Dict:
        prompt = f"""
            You are a senior Site Reliability Engineer performing structured root cause analysis.

            {context}

SYSTEM BASELINE ASSUMPTIONS:
- CPU usage baseline: < 70%
- Memory usage baseline: < 75%
- Disk usage baseline: < 80%
- Any metric above 100% is invalid and indicates monitoring error.

Your task:
1. Identify the most likely root cause.
2. List affected services.
3. Provide a confidence score between 0 and 1.
4. Provide clear remediation steps.

CRITICAL OUTPUT RULES:
- Return ONLY a raw JSON object.
- No explanations.
- No reasoning text.
- No <think> blocks.
- No markdown.
- Output must start with '{{' and end with '}}'.

Required JSON keys:
root_cause, affected_services, confidence, fixes
"""

        try:
            response = await self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_completion_tokens=2048,
                top_p=0.9,
                stream=False
            )

            content = response.choices[0].message.content.strip()

           
            matches = re.findall(r"\{[\s\S]*?\}", content)

            if not matches:
                raise ValueError("No JSON object found in LLM output")
            json_text = matches[-1]  
            parsed = json.loads(json_text)
            
            return parsed

        except Exception as e:
            print("RCA PARSE ERROR:", str(e))

            return {
                "root_cause": "Invalid LLM JSON response",
                "affected_services": [],
                "confidence": 0.0,
                "fixes": []
            }
