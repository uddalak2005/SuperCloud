import os
import json
import time
import requests
from datetime import datetime, timezone

# Paths
BASE_DIR = os.getcwd()
FIFO_PATH = os.path.join(BASE_DIR, "agent/fifo/primary.fifo")
LOG_FIFO = os.path.join(BASE_DIR, "agent/fifo/logs.fifo")



BACKEND_URL = "http://orchestrator:8000/anomaly"
HOSTNAME = os.uname().nodename
WEBSOCKET_BACKEND_URL = "http://orchestrator:8000/ws"


def log(msg):
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")
    
log(FIFO_PATH)
log(LOG_FIFO)


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
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "host": HOSTNAME,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "metrics": original_data,
        "logs": logs
    }

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=5)
        log(f"Sent {anomaly_type} → Backend status: {response.status_code}")
    except Exception as e:
        log(f"BACKEND ERROR: {e}")


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

        # send ALL logs to websocket backend
        try:
            response = requests.post(WEBSOCKET_BACKEND_URL, json=logs, timeout=5)
            log(f"Sent logs to websocket backend status: {response.status_code}")
        except Exception as e:
            log(f"WEBSOCKET BACKEND ERROR: {e}")

        # Detect anomaly
        anomalies = detect_anomaly(data, logs)

        # Send to backend if anomalies exist
        for anomaly_type, severity in anomalies:
            send_to_backend(data, anomaly_type, severity, logs)

        time.sleep(5)


if __name__ == "__main__":
    main()