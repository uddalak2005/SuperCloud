
from typing import Dict, Any, List
import uuid
import numpy as np
from datetime import datetime, timezone



from base_agent import BaseAgent




class WatcherAgent(BaseAgent):

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "watcher")
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.anomaly_threshold = 3.0

    async def get_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect anomalies from telemetry input
        """
        service = state.get("service","unknown")
        metrics = state.get("metrics",{})

        if not metrics:
            return {
                "action": "monitor",
                "message": "No metrics received"
            }

        anomalies = self.detect_anomalies(metrics)
        self.update_baseline(metrics)

        if anomalies:
            severity = self.calculate_severity(anomalies)
            return {
                "action": "alert",
                "incident_id": self.generate_incident_id(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "parameters": {
                    "service": service,
                    "anomalies": anomalies,
                    "severity": severity,
                    "trigger_rca": True
                }
            }
        return {
            "action": "monitor",
            "timestamp":datetime.now(timezone.utc).isoformat(),
        }

    def detect_anomalies(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        anomalies = []

        for metric_name, value in metrics.items():

            if metric_name not in self.baseline_metrics:
                continue

            baseline = self.baseline_metrics[metric_name]

            std = max(baseline["std"], 1e-5)
            z_score = (value - baseline["mean"]) / std

            if abs(z_score) > self.anomaly_threshold:
                confidence = min(abs(z_score) / self.anomaly_threshold, 1.0)

                anomalies.append({
                    "metric": metric_name,
                    "current_value": value,
                    "expected_value": baseline["mean"],
                    "z_score": round(z_score, 2),
                    "confidence": round(confidence, 2)
                })

        return anomalies

# for detecting anomalies and updating baselines based on incoming metrics 


    def update_baseline(self, metrics: Dict[str, float]):

        learning_rate = 0.1

        for metric_name, value in metrics.items():

            if metric_name not in self.baseline_metrics:
                self.baseline_metrics[metric_name] = {
                    "mean": value,
                    "std": 1.0
                }
                continue

            baseline = self.baseline_metrics[metric_name]
            new_mean = (1 - learning_rate) * baseline["mean"] + learning_rate * value

            new_std = np.sqrt(
                (1 - learning_rate) * (baseline["std"] ** 2)
                + learning_rate * ((value - new_mean) ** 2)
            )

            self.baseline_metrics[metric_name]["mean"] = new_mean
            self.baseline_metrics[metric_name]["std"] = new_std




    def calculate_severity(self, anomalies: List[Dict[str, Any]]) -> str:

        max_z = max(abs(a["z_score"]) for a in anomalies)
        if max_z >= 6:
            return "critical"
        elif max_z >= 4:
            return "high"
        elif max_z >= 3:
            return "medium"
        else:
            return "low"

    def generate_incident_id(self) -> str:
        return f"INC-{uuid.uuid4().hex[:8].upper()}"
