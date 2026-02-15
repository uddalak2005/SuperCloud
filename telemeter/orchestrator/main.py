import os
import json
import time
import requests
from datetime import datetime

FIFO_PATH = "../agent/fifo/primary.fifo"
LOG_FIFO = "../agent/fifo/logs.fifo"
BACKEND_URL = "http://backend:8000/anomaly"
HOSTNAME = os.uname().nodename


def log(msg):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def detect_anomaly(data, logs):
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
        f"NET TX: {network.get('tx_bytes_per_sec', 0)} | "
        f"LOG : {logs}") 

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
        
    #Logs
    if logs.get("level", "") == "ERROR" or logs.get("level", "") == "WARN" :
        anomalies.append(("Logs", logs))

    if anomalies:
        log(f"Anomaly detected: {anomalies}")
    else:
        log("No anomaly detected")

    return anomalies


def send_to_backend(original_data, anomaly_type, severity, logs):
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "host": HOSTNAME,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "metrics": original_data,
        "logs" : logs
    }

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=5)
        log(f"Sent {anomaly_type} → Backend status: {response.status_code}")
    except Exception as e:
        log(f"BACKEND ERROR: {e}")


def main():
    log("Orchestrator Started...")

    while True:
        data = {}
        logs = {}
        new_log_received = False

        log("Waiting for FIFO data...")

        try:
            with open(FIFO_PATH, "r") as fifo:
                line = fifo.readline()
                if line:
                    log(f"Raw Data: {line.strip()}")
                    data = json.loads(line.strip())
        except Exception as e:
            log(f"FIFO_PATH ERROR: {e}")
            time.sleep(2)
            continue

        try:
            fd = os.open(LOG_FIFO, os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(fd) as fifo:
                while True:
                    line = fifo.readline()
                    if not line:
                        break 

                    log(f"Raw Log Data: {line.strip()}")
                    logs = json.loads(line.strip())
                    new_log_received = True

        except Exception as e:
            log(f"LOG_FIFO ERROR: {e}")

        if new_log_received:
            anomalies = detect_anomaly(data, logs)

            if anomalies:
                log(f"Anomaly detected: {anomalies}")

                for anomaly_type, severity in anomalies:
                    try:
                        send_to_backend(data, anomaly_type, severity, logs)
                    except Exception as e:
                        log(f"BACKEND ERROR: {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
