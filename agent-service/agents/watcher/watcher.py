
from base_agent import BaseAgent
from typing import Dict, Any, List
import numpy as np

class WatcherAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "watcher")
        self.baseline_metrics = {}  #define baseline metrics for anomaly detection from user input.
        self.anomaly_threshold = 3.0  
    
    async def get_action(self, state: str) -> Dict[str, Any]:



        """
        This continuously monitor and detect anomalies.

        state will contain current metrics, logs, and other relevant info. For simplicity, we will just focus on metrics here.
        state will be passed as string by the orchestrator, so we will need to parse it to extract the metrics.state is String
        as we know Node sends serialized JSON. So we can parse it using json.loads to get the actual metrics data structure.
        """



        # Parse current metrics from state (input) using a datastreamer or a POST method from orchestrator/ telementry connector.
        current_metrics = self.parse_metrics(state)
        
        # Check for anomalies
        anomalies = self.detect_anomalies(current_metrics)
        
        if anomalies:
            return {
                "action": "alert",
                "parameters": {
                    "anomalies": anomalies,
                    "severity": self.calculate_severity(anomalies),
                    "trigger_rca": True
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
    
    #have to define parse_metrics and calculate_severity for the above code to work, but skipping for now since it's not the main focus of this agent
    








    #basic detection logic
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
