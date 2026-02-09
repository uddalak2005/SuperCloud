
import json
from base_agent import BaseAgent
import openai
from typing import Dict, Any, List

class RCABrainAgent(BaseAgent):
    def __init__(self, agent_id: str, llm_model: str = "gpt-4"):
        super().__init__(agent_id, "rca_brain")
        self.llm_model = llm_model
        self.dependency_graph = {}
    
    async def get_action(self, state: str) -> Dict[str, Any]:
        """
        Perform root cause analysis using LLM reasoning + dependency graphs
        """
        # Extract relevant information
        incident_data = self.parse_incident_data(state)


        
        """ 'parse_incident_data' is not defined but it should extract things like affected services,
          error messages, timestamps, etc from the state input. Skipping implementation for now since 
          it's not the main focus of this agent."""


        # Build investigation context
        investigation_context = await self.build_investigation_context(
            incident_data
        )
        
        # Use LLM for reasoning
        rca_result = await self.perform_llm_reasoning(
            investigation_context
        )
        
        # Validate against dependency graph
        validated_rca = self.validate_with_dependencies(rca_result)
        
        return {
            "action": "rca_complete",
            "parameters": {
                "root_cause": validated_rca["root_cause"],
                "affected_services": validated_rca["affected_services"],
                "confidence": validated_rca["confidence"],
                "recommended_fixes": validated_rca["fixes"]
            }
        }
    
    async def build_investigation_context(self, incident_data: Dict) -> str:
        """
        Gather logs, metrics, traces for comprehensive analysis, here also methods not done
        get logs, metrics,traces from prometheus,loki, tempo, and also get dependency info from the dependency graph. 
        Then combine all this into a single context string for the LLM to analyze.


        DO THIS MODULE @UDDALAK 

        """
        context_parts = []
        
        # Get logs from affected services
        logs = await self.get_logs(incident_data["services"])
        context_parts.append(f"LOGS:\n{logs}")
        
        # Get metrics
        metrics = await self.get_metrics(incident_data["services"])
        context_parts.append(f"METRICS:\n{metrics}")
        
        # Get traces
        traces = await self.get_traces(incident_data["trace_ids"])
        context_parts.append(f"TRACES:\n{traces}")
        
        # Get dependency info
        deps = self.get_dependency_info(incident_data["services"])
        context_parts.append(f"DEPENDENCIES:\n{deps}")
        
        return "\n\n".join(context_parts)
    



    
    async def perform_llm_reasoning(self, context: str) -> Dict:
        """
        Use LLM to reason about root cause
        """
        prompt = f"""
        You are an expert SRE performing root cause analysis.
        
        INCIDENT CONTEXT:
        {context}
        
        Analyze the above data and provide:
        1. Root cause identification
        2. Affected services
        3. Confidence level (0-1)
        4. Recommended remediation steps
        
        Format your response as JSON.
        """
        
        client = openai.AsyncOpenAI()

        response = await client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content

        try:
            rca_result = json.loads(content)
        except Exception:
            rca_result = {
                "root_cause": {"service": "unknown"},
                "affected_services": [],
                "confidence": 0.0,
                "fixes": []
        }
            
        return rca_result

    def get_downstream_services(self, service: str) -> List[str]:
        """
        Find services that depend on the given service
        """

        downstream = []

        for svc, dependencies in self.dependency_graph.items():
            if service in dependencies:
                downstream.append(svc)

        return downstream
    
    def validate_with_dependencies(self, rca_result: Dict) -> Dict:
        """
        Cross-reference LLM findings with dependency graph
        """
        root_cause_service = rca_result["root_cause"]["service"]
        
        # Check if downstream services are affected
        downstream = self.get_downstream_services(root_cause_service)
        
        # Validate affected services match dependency chain
        rca_result["validated"] = all(
            svc in downstream 
            for svc in rca_result["affected_services"]
        )
        
        return rca_result
