from base_agent import BaseAgent
from typing import Dict, Any, List
import numpy as np



class DetectorAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "detector")
        self.baseline_metrics = {}
        #     {
        #      "detector": {
        #         "baseline_metrics": {
        #             "cpu_usage_percent": {"mean": 45.0, "std": 15.0},
        #             "memory_usage_percent": {"mean": 60.0, "std": 10.0},
        #             "response_time_ms": {"mean": 150.0, "std": 50.0}
        #         }
        #     }
        # }
     #define baseline metrics for anomaly detection from user input.
        self.anomaly_threshold = 3.0  
    
    async def get_action(self,state: Dict[str, Any]) -> Dict[str, Any]:


        """
        This continuously monitor and detect anomalies.

        state will contain current metrics, logs, and other relevant info. For simplicity, we will just focus on metrics here.
        state will be passed as string by the orchestrator, so we will need to parse it to extract the metrics.state is String
        as we know Node sends serialized JSON. So we can parse it using json.loads to get the actual metrics data structure.
        """
        

        # Parse current metrics from state (input) using datadog from orchestrator/ telementry connector.
                # Parse current metrics from state (input) using datadog from orchestrator/ telementry connector.
        current_metrics = state 

        for k, v in state.items():
            current_metrics[k] = v

        
        # Check for anomalies
        anomalies = self.detect_anomalies(current_metrics)
        
        if anomalies:
            return {
                "action": "alert",
                "parameters": {
                    "anomalies": anomalies,
                    "severity": self.calculate_severity(anomalies),
                    "trigger_rca": self.calculate_severity(anomalies) in ["HIGH", "CRITICAL"]  # singal to the orchestrator to trigger RCA agent for deeper investigation
                }
            }
        
        # Continue monitoring
        return {
            "action": "get_metrics",
            "parameters": {
                "services": ["all"],
                "interval": "30s"
            }
        }
    #the following code is a pseudo code to show how the agent can instruct the orchestrator to wait for a certain interval before the next check, but since we don't have the actual implementation of the orchestrator right now.
    # interval = parse_time(result["parameters"]["next_check"])
    # await asyncio.sleep(interval)

    #have to define parse_metrics for the above code to work, but skipping for now since it's not the main focus of this agent.
    


    #basic detection logic, assumes numerical metrics and uses z-score for anomaly detection, later i change the logic.
    def detect_anomalies(self, metrics: Dict) -> List[Dict]:
        """
        anomaly detection
        """
        anomalies = []
        for metric_name, value in metrics.items():
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]
                z_score = (value - baseline['mean']) / baseline['std']
                
                if abs(z_score) > self.anomaly_threshold:
                    anomalies.append({
                        "metric": metric_name,
                        "current_value": value,
                        "expected_value": baseline['mean'],
                        "z_score": z_score
                    })
        
        return anomalies
    

    def calculate_severity(self, anomalies: List[Dict]) -> str:
        """
        Calculate severity level based on anomaly z-scores
        """

        if not anomalies:
            return "LOW"

        max_z = max(abs(a.get("z_score", 0)) for a in anomalies)

        if max_z > 6:
            return "CRITICAL"
        elif max_z > 4:
            return "HIGH"
        elif max_z > 2:
            return "MEDIUM"
        else:
            return "LOW"                             