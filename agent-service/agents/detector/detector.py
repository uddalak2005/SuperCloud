from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import numpy as np


class DetectorAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "detector")

        # Static statistical limits 
        self.cpu_threshold = 85
        self.memory_threshold = 85
        self.disk_threshold = 90
        self.network_threshold = 3000  


    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:

        features = self.extract_features(telemetry_payload)

        if features is None:
            return self.no_action_response()

        anomaly, score = self.detect_statistical_anomaly(features)

        if anomaly:
            severity = self.calculate_severity(score)

            return {
                "action": "alert",
                "parameters": {
                    "anomaly_score": float(score),
                    "severity": severity,
                    "trigger_rca": severity in ["HIGH", "CRITICAL"],
                    "features": {
                        "cpu_percent": features[0],
                        "memory_percent": features[1],
                        "disk_percent": features[2],
                        "rx_bytes_per_sec": features[3],
                        "tx_bytes_per_sec": features[4],
                    }
                }
            }

        return self.no_action_response()


    def extract_features(self, payload: Dict[str, Any]) -> List[float] | None:
        try:
            metrics = payload.get("metrics", {})

            cpu = float(metrics["cpu"]["cpu_percent"])
            memory = float(metrics["memory"]["used_percent"])
            disk = float(metrics["disk"]["used_percent"])
            rx = float(metrics["network"]["rx_bytes_per_sec"])
            tx = float(metrics["network"]["tx_bytes_per_sec"])

            return [cpu, memory, disk, rx, tx]

        except Exception:
            return None


    def detect_statistical_anomaly(self, features: List[float]):

        cpu, memory, disk, rx, tx = features
        score = 0.0

        weights = {
            "cpu": 1.5,
            "memory": 2.0,
            "disk": 1.8,
            "network": 1.0
        }

        if cpu > self.cpu_threshold:
            deviation = (cpu - self.cpu_threshold) / 100
            score += deviation * weights["cpu"]

        if memory > self.memory_threshold:
            deviation = (memory - self.memory_threshold) / 100
            score += deviation * weights["memory"]

        if disk > self.disk_threshold:
            deviation = (disk - self.disk_threshold) / 100
            score += deviation * weights["disk"]

        network_deviation = 0
        if rx > self.network_threshold:
            network_deviation += (rx - self.network_threshold) / 10000

        if tx > self.network_threshold:
            network_deviation += (tx - self.network_threshold) / 10000

        score += network_deviation * weights["network"]

        is_anomaly = score > 0.05   

        return is_anomaly, score


    def calculate_severity(self, score: float) -> str:

        if score > 0.5:
            return "CRITICAL"
        elif score > 0.30:
            return "HIGH"
        elif score > 0.15:
            return "MEDIUM"
        else:
            return "LOW"



    def no_action_response(self) -> Dict[str, Any]:
        return {
            "action": "get_metrics",
            "parameters": {
                "services": ["all"],
                "interval": "30s"
            }
        }
