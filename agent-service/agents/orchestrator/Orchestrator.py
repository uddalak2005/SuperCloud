import httpx
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, cast


class IncidentState(Enum):
    MONITORING = "monitoring"
    ANOMALY_DETECTED = "anomaly_detected"
    RCA_IN_PROGRESS = "rca_in_progress"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"


class Orchestrator:

    def __init__(
        self,
        incident_logger=None,
        config: Optional[Dict[str, Any]] = None,
        websocket_manager=None
    ):
        self.logger = incident_logger
        self.config = config or self._default_config()

        self.detector_service_url = self.config.get("detector_service_url")
        self.rca_service_url = self.config.get("rca_service_url")
        self.fixer_service_url = self.config.get("fixer_service_url")
        self.websocket_manager = websocket_manager

        self.active_incidents: Dict[str, Dict[str, Any]] = {}

    def _default_config(self) -> Dict[str, Any]:
        return {
            "enable_auto_remediation": False, #change to True to enable auto remediation
            "detector_service_url": "http://detector:8001",
            "rca_service_url": "http://rca:8002",
            "fixer_service_url": "http://fixer:8003"
        }

    async def process_telemetry(self, telemetry_payload: Dict[str, Any]) -> Dict[str, Any]:

        detection_result = await self._run_detection(telemetry_payload)
        print("DETECTION RESULT:", detection_result)

        if detection_result.get("action") == "alert":
            await self._handle_incident(detection_result, telemetry_payload)

        return {"status": "processed"}

    async def _run_detection(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.detector_service_url}/detect",
                    json=telemetry_data,
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            print(f"[Orchestrator] Detector service error: {e}")
            return {"action": "error", "error": str(e)}

    async def _handle_incident(
        self,
        detection_result: Dict[str, Any],
        telemetry_data: Dict[str, Any]
    ):

        incident_id = str(uuid.uuid4())

        print(f"\n[Orchestrator] INCIDENT DETECTED: {incident_id}\n")

        incident_record = {
            "incident_id": incident_id,
            "state": IncidentState.ANOMALY_DETECTED.value,
            "detection_time": datetime.now(timezone.utc).isoformat(),
            "detection_result": detection_result,
            "telemetry_snapshot": telemetry_data,
            "timeline": []
        }

        self.active_incidents[incident_id] = incident_record

        params = cast(Dict[str, Any], detection_result.get("parameters", {}))
        trigger_rca = params.get("trigger_rca", False)

        if trigger_rca:
            await self._run_rca_pipeline(incident_id)
        else:
            await self._alert_only(incident_id)

    async def _run_rca_pipeline(self, incident_id: str):

        incident = self.active_incidents[incident_id]
        incident["state"] = IncidentState.RCA_IN_PROGRESS.value

        params = cast(Dict[str, Any], incident.get("detection_result", {}).get("parameters", {}))

      
        rca_state = {
            "incident_id": incident_id,
            "severity": params.get("severity", "low"),
            "anomaly_score": params.get("anomaly_score", 0.0),
            "metrics": incident.get("telemetry_snapshot", {}).get("metrics", {}),
            "logs": incident.get("telemetry_snapshot", {}).get("logs", {})
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rca_service_url}/analyze",
                    json=rca_state,
                    timeout=20
                )

                response.raise_for_status()
                rca_result = response.json()

                print(f"[Orchestrator RCA RESULT] {incident_id}: \n", rca_result)

            if "parameters" not in rca_result:
                raise ValueError("Invalid RCA response format")

            incident["rca_result"] = rca_result
            incident["state"] = IncidentState.RCA_IN_PROGRESS.value

            incident["timeline"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "rca_completed",
                "details": rca_result
            })

            if self.config.get("enable_auto_remediation", False):  #Auto remediation toggle
                await self._auto_remediate(incident_id)
            else:
                await self._log_incident(incident_id)

        except Exception as e:
            print(f"[Orchestrator] RCA service error \n: {e}")
            incident["state"] = IncidentState.FAILED.value
            await self._log_incident(incident_id)

    #FIXER endpont

    async def _auto_remediate(self, incident_id: str):

        incident = self.active_incidents.get(incident_id)
        if not incident:
            return

        incident["state"] = IncidentState.REMEDIATION_IN_PROGRESS.value

        rca_payload = incident.get("rca_result", {}).get("parameters", {})

        print(f"[Orchestrator] Sending to Fixer for incident {incident_id}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.fixer_service_url}/execute",
                    json=rca_payload,
                    timeout=30
                )
                response.raise_for_status()

                fixer_result = response.json()
                print(f"[Fixer RESULT] {incident_id}:", fixer_result)

            incident["state"] = IncidentState.RESOLVED.value

            incident["timeline"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "remediation_completed",
                "details": fixer_result
            })

            await self._log_incident(incident_id)

        except Exception as e:
            print(f"[Orchestrator] Fixer error: {e}")
            incident["state"] = IncidentState.FAILED.value
            await self._log_incident(incident_id)


    async def _alert_only(self, incident_id: str):
        await self._log_incident(incident_id)
        self.active_incidents.pop(incident_id, None)

    async def _log_incident(self, incident_id: str):
        incident = self.active_incidents.get(incident_id)
        if incident and self.logger:
            await self.logger.log_incident(incident)

    def get_status(self) -> Dict[str, Any]:
        return {
            "config": self.config,
            "active_incidents": len(self.active_incidents)
        }




# Added by Souherdya - Websocket for UI Updates
# -----------------------------------------------------------------------------


from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import deque
import asyncio

class WebSocketManager:
    def __init__(self, buffer_size: int = 5000):
        self.active_connections: List[WebSocket] = []
        self.event_buffer = deque(maxlen=buffer_size)
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)

        # Replay buffered events to new client
        for event in self.event_buffer:
            await websocket.send_json(event)

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Create an event and broadcast it
        """
        message = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        # Store for replay
        self.event_buffer.append(message)

        await self._broadcast(message)

    async def _broadcast(self, message: Dict[str, Any]):
        dead_connections = []

        async with self.lock:
            for ws in self.active_connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_connections.append(ws)

            # Cleanup dead sockets
            for ws in dead_connections:
                self.active_connections.remove(ws)