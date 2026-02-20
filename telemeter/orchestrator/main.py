import os
import json
import time
import requests
from datetime import datetime, timezone
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from fixer.fixer import Fixer
import websocket

fixer = Fixer()

# Paths
BASE_DIR = os.getcwd()
FIFO_PATH = os.path.join(BASE_DIR, "agent/fifo/primary.fifo")
LOG_FIFO = os.path.join(BASE_DIR, "agent/fifo/logs.fifo")



BACKEND_URL = "http://orchestrator:8000/anomaly"
HOSTNAME = os.uname().nodename
# WEBSOCKET_BACKEND_URL = "http://orchestrator:8000/ws"


def log(msg):
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")
    
log(FIFO_PATH)
log(LOG_FIFO)

def handle_backend_response(response: dict):

    action = response.get("action")

    if action == "alert_only":
        print("ALERT ONLY:", response.get("reason"))
        return

    if action == "execute_fix":

        fix_payload = response.get("fix_payload")

        if not fix_payload:
            print("No fix payload received")
            return

        print(f"Executing fix for issue: {fix_payload.get('issue_type')}")

        fix_result = fixer.handle_incident(fix_payload)

        print("Fix result:", fix_result)
        return

    print("Unknown backend action:", action)


def detect_anomaly(data, logs):
    anomalies = []

    cpu = data.get("cpu", {})
    memory = data.get("memory", {})
    disk = data.get("disk", {})
    network = data.get("network", {})

    log(
        f"CPU: {cpu.get('cpu_percent', 0)}% | "
        f"MEM: {memory.get('used_percent', 0)}% | "
        f"DISK: {disk.get('used_percent', 0)}% | "
        f"NET RX: {network.get('rx_bytes_per_sec', 0)} | "
        f"NET TX: {network.get('tx_bytes_per_sec', 0)} | "
        f"LOG LEVEL: {logs.get('level', 'N/A')}"
    )

    # CPU
    if cpu.get("cpu_percent", 0) > 90:
        anomalies.append(("cpu_high", "critical"))
    elif cpu.get("cpu_percent", 0) > 80:
        anomalies.append(("cpu_spike", "warning"))

    # Memory
    if memory.get("used_percent", 0) > 90:
        anomalies.append(("memory_critical", "critical"))
    elif memory.get("used_percent", 0) > 80:
        anomalies.append(("memory_high", "warning"))

    # Disk
    if disk.get("used_percent", 0) > 85:
        anomalies.append(("disk_high", "critical"))

    # Network
    if network.get("rx_bytes_per_sec", 0) > 10_000_000:
        anomalies.append(("network_rx_spike", "warning"))
    if network.get("tx_bytes_per_sec", 0) > 10_000_000:
        anomalies.append(("network_tx_spike", "warning"))

    # Logs
    if logs.get("level") in ["ERROR", "WARN"]:
        anomalies.append(("log_issue", "warning"))

    if anomalies:
        log(f"Anomaly detected: {anomalies}")
    else:
        log("No anomaly detected")

    return anomalies


def send_to_backend(original_data, anomaly_type, severity, logs):

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": HOSTNAME,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "metrics": original_data,
        "logs": logs
    }

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=5)

        log(f"Sent {anomaly_type} → Backend status: {response.status_code}")

        if response.status_code != 200:
            log("Backend returned non-200 status")
            return {"action": "alert_only", "reason": "backend_error"}

        try:
            return response.json()
        except Exception:
            log("Invalid JSON from backend")
            return {"action": "alert_only", "reason": "invalid_backend_json"}

    except Exception as e:
        log(f"BACKEND ERROR: {e}")
        return {"action": "alert_only", "reason": "backend_unreachable"}


def read_fifo_blocking(path):
    try:
        with open(path, "r") as fifo:
            line = fifo.readline()
            if line:
                return json.loads(line.strip())
    except Exception as e:
        log(f"FIFO READ ERROR ({path}): {e}")
    return {}


def read_log_fifo_nonblocking(path):
    logs = {}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd) as fifo:
            while True:
                line = fifo.readline()
                if not line:
                    break
                logs = json.loads(line.strip())
    except BlockingIOError:
        pass
    except Exception as e:
        log(f"LOG FIFO ERROR: {e}")

    return logs


def main():
    log("Orchestrator Started...")

    while True:
        log("Waiting for FIFO data...")

        # Read metrics
        data = read_fifo_blocking(FIFO_PATH)

        if not data:
            time.sleep(2)
            continue

        log(f"Raw Data: {data}")

        # Read logs (non-blocking)
        logs = read_log_fifo_nonblocking(LOG_FIFO)
        log(logs)
        if logs:
            try:
                requests.post(
                "http://orchestrator:8000/internal/event",
                data=json.dumps({"type": "logs", "data": logs}),
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            except Exception as e:
                log(f"WEBSOCKET BACKEND ERROR: {e}")

        # Detect anomaly
        anomalies = detect_anomaly(data, logs)

        # Send to backend if anomalies exist
        for anomaly_type, severity in anomalies:
            backend_response = send_to_backend(data, anomaly_type, severity, logs)
            print(backend_response)
            handle_backend_response(backend_response)
        time.sleep(5)


if __name__ == "__main__":
    main()