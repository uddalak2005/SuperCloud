from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import uvicorn

from .detector import DetectorAgent

app = FastAPI()

detector = DetectorAgent(agent_id="detector-service-001")

detector.baseline_metrics = {
    "cpu_usage_percent": {"mean": 45, "std": 12},
    "memory_usage_percent": {"mean": 55, "std": 10},
    "disk_io_ops": {"mean": 350, "std": 120},
    "network_throughput_mbps": {"mean": 45, "std": 20},
    "http_request_rate": {"mean": 180, "std": 70},
    "error_rate_percent": {"mean": 1.0, "std": 0.6},
    "response_time_ms": {"mean": 180, "std": 60},
    "db_connection_pool": {"mean": 40, "std": 15},
}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "detector"}


@app.post("/detect")
async def detect(state: Dict[str, Any]):
    try:
        return await detector.get_action(state)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("service:app", host="0.0.0.0", port=8001, reload=True)
