# agents/rca_brain.py
import json
from base_agent import BaseAgent
from groq import AsyncGroq
from typing import Dict, Any



class RCABrainAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "rca_brain")
        

    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform root cause analysis using LLM reasoning over incident context
        """

        # Build investigation context directly from incident state
        investigation_context = self.build_investigation_context(state)

        # Use LLM for reasoning
        rca_result = await self.perform_llm_reasoning(
            investigation_context
        )

        return {
            "action": "rca_complete",
            "parameters": {
                "root_cause": rca_result.get("root_cause"),
                "affected_services": rca_result.get("affected_services", []),
                "confidence": rca_result.get("confidence", 0.0),
                "recommended_fixes": rca_result.get("fixes", [])
            }
        }

    def build_investigation_context(self, state: Dict[str, Any]) -> str:
        """
        Build RCA investigation context directly from incident state dict
        """

        try:
            pretty_state = json.dumps(state, indent=2, default=str)
        except Exception:
            pretty_state = str(state)

        context = f"""
            Below is the full incident telemetry state detected by the monitoring system.

            INCIDENT STATE:
            {pretty_state}
            Use this information to perform root cause analysis.
            """
        return context      

    async def perform_llm_reasoning(self, context: str) -> Dict:
        """
        Use LLM to reason about root cause
        """

        prompt = f"""
            You are an expert Site Reliability Engineer.

            Below is an incident detected by an automated monitoring system.

            {context}

            Your task:
            1. Identify the most likely root cause
            2. List affected services
            3. Provide a confidence score (0-1)
            4. Recommend concrete remediation steps

            Respond ONLY in valid JSON with keys:
            root_cause, affected_services, confidence, fixes
            """

        client = AsyncGroq()

        response = await client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        reasoning_effort="default",
        stream=False   
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except Exception:
            return {
                "root_cause": "Unable to determine",
                "affected_services": [],
                "confidence": 0.0,
                "fixes": []
         }
