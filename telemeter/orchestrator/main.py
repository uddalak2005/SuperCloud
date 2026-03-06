import os
import json
import time
import requests
from datetime import datetime, timezone
import sys
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from fixer.fixer import Fixer

fixer = Fixer()

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
    

METRICS_MODE = "simulated" #real
 
SIMULATION_CYCLE_MINUTES = 2

SIMULATION_START_TIME = time.time()

def get_current_simulation_profile():
    """
    Cycles through:
    normal → degraded → outage
    Each lasting SIMULATION_CYCLE_MINUTES
    """

    elapsed_seconds = time.time() - SIMULATION_START_TIME
    elapsed_minutes = int(elapsed_seconds // 60)

    cycle_index = (elapsed_minutes // SIMULATION_CYCLE_MINUTES) % 3

    if cycle_index == 0:
        return "normal"
    elif cycle_index == 1:
        return "degraded"
    else:
        return "outage"


def generate_simulated_metrics():
    """
    Generates fake metrics for testing.
    Profiles:
    - normal
    - degraded
    - outage
    """
    
    profile = "outage"

    if profile == "normal":
        cpu = random.uniform(5, 25)
        mem = random.uniform(30, 60)
        disk = random.uniform(20, 50)
        rx = random.randint(100, 5000)
        tx = random.randint(100, 5000)

    elif profile == "degraded":
        cpu = random.uniform(60, 85)
        mem = random.uniform(70, 90)
        disk = random.uniform(50, 80)
        rx = random.randint(50_000, 200_000)
        tx = random.randint(50_000, 200_000)

    elif profile == "outage":
        cpu = random.uniform(95, 100)
        mem = random.uniform(90, 98)
        disk = random.uniform(80, 95)
        rx = random.randint(5_000_000, 20_000_000)
        tx = random.randint(5_000_000, 20_000_000)

    else:
        cpu = 10
        mem = 40
        disk = 30
        rx = 1000
        tx = 1000

    return {
        "timestamp": int(time.time()),
        "cpu": {"cpu_percent": round(cpu, 2)},
        "memory": {"used_percent": round(mem, 2)},
        "disk": {"used_percent": round(disk, 2)},
        "network": {
            "rx_bytes_per_sec": rx,
            "tx_bytes_per_sec": tx
        }
    }


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
        print(METRICS_MODE)

        # Read metrics
        if METRICS_MODE == "simulated":
            data = generate_simulated_metrics()
            print(data)
        else:
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
            backend_response = send_to_backend(data, anomaly_type, severity, logs)
            print(backend_response)
            handle_backend_response(backend_response)
        time.sleep(5)


if __name__ == "__main__":
    main()