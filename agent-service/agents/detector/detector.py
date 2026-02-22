from agents.base_agent import BaseAgent
from typing import Dict, Any, List


class DetectorAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "detector")

        self.cpu_threshold = 75
        self.memory_threshold = 75
        self.disk_threshold = 85
        self.network_threshold = 20000

    async def get_action(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:
        features = self.extract_features(telemetry_payload)

        if features is None:
            return self.no_action_response()

        statistical_anomaly, statistical_score = self.detect_statistical_anomaly(features)

        logs = telemetry_payload.get("logs", {})
        log_score = self.calculate_log_anomaly_score(logs)

        final_score = round(statistical_score + log_score, 4)
        is_anomaly = final_score > 0.05

        if is_anomaly:
            severity = self.calculate_severity(final_score)

            return {
                "action": "alert",
                "parameters": {
                    "anomaly_score": float(final_score),
                    "statistical_score": float(statistical_score),
                    "log_score": float(log_score),
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

        def relative_deviation(value, threshold):
            if value <= threshold:
                return 0.0
            return (value - threshold) / threshold

        score += relative_deviation(cpu, self.cpu_threshold) * weights["cpu"]
        score += relative_deviation(memory, self.memory_threshold) * weights["memory"]
        score += relative_deviation(disk, self.disk_threshold) * weights["disk"]

        total_network = rx + tx
        score += relative_deviation(total_network, self.network_threshold) * weights["network"]

        score = round(score, 4)
        is_anomaly = score > 0.02

        return is_anomaly, score

    def calculate_log_anomaly_score(self, logs: Any) -> float:
        if not logs:
            return 0.0

        level_weights = {
            "INFO": 0.0,
            "WARNING": 0.1,
            "ERROR": 0.3,
            "CRITICAL": 0.6
        }

        log_score = 0.0
        error_count = 0

        if isinstance(logs, dict):
            level = logs.get("level", "").upper()
            log_score += level_weights.get(level, 0.0)
            if level in ["ERROR", "CRITICAL"]:
                error_count += 1

        elif isinstance(logs, list):
            for log in logs:
                level = log.get("level", "").upper()
                log_score += level_weights.get(level, 0.0)
                if level in ["ERROR", "CRITICAL"]:
                    error_count += 1

        if error_count > 3:
            log_score *= 1.5
        elif error_count > 1:
            log_score *= 1.2

        return round(min(log_score, 1.0), 4)

    def calculate_severity(self, score: float) -> str:
        if score > 0.7:
            return "CRITICAL"
        elif score > 0.4:
            return "HIGH"
        elif score > 0.2:
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