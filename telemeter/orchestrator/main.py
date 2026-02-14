import os
import json
import time
import requests
from datetime import datetime, timezone

BASE_DIR = os.getcwd()
FIFO_PATH = os.path.join(BASE_DIR, "agent/fifo/primary.fifo")
BACKEND_URL ="http://host.docker.internal:8000/anomaly"
HOSTNAME = os.uname().nodename


def log(msg):
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")


def detect_anomaly(data):
    anomalies = []

    cpu = data.get("cpu", {})
    memory = data.get("memory", {})
    disk = data.get("disk", {})
    network = data.get("network", {})

    # Print current metrics snapshot
    log(f"CPU: {cpu.get('cpu_percent', 0)}% | "
        f"MEM: {memory.get('used_percent', 0)}% | "
        f"DISK: {disk.get('used_percent', 0)}% | "
        f"NET RX: {network.get('rx_bytes_per_sec', 0)} | "
        f"NET TX: {network.get('tx_bytes_per_sec', 0)}")

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

    if anomalies:
        log(f" Anomaly detected: {anomalies}")
    else:
        log(" No anomaly detected")

    return anomalies


def send_to_backend(original_data, anomaly_type, severity):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "host": HOSTNAME,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "metrics": original_data
    }

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=5)
        log(f" Sent {anomaly_type} → Backend status: {response.status_code}")
    except Exception as e:
        log(f" BACKEND ERROR: {e}")


def main():
    log(" Orchestrator Started...")

    while True:
        log(" Waiting for FIFO data...")

        with open(FIFO_PATH, "r") as fifo:
            for line in fifo:
                try:
                    log(f" Raw Data: {line.strip()}")

                    data = json.loads(line.strip())

                    anomalies = detect_anomaly(data)

                    for anomaly_type, severity in anomalies:
                        send_to_backend(data, anomaly_type, severity)

                except Exception as e:
                    log(f" BACKEND ERROR: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
