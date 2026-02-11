"""
Orchestrator - Central coordination service for autonomous incident management
Coordinates: telemetry collection -> detection -> RCA -> remediation -> logging
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, cast
from enum import Enum
import uuid
from fastapi import params
import httpx
from telemetry_connector import TelemetryConnector



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
        telemetry_connector: TelemetryConnector,      
        incident_logger=None,
        config: Dict[str, Any] = None
    ):

        self.telemetry = telemetry_connector
        self.logger = incident_logger

        self.config = config or self._default_config()

        # Service URLs for external agents
        self.detector_service_url = self.config.get("detector_service_url")
        self.rca_service_url = self.config.get("rca_service_url")
        self.fixer_service_url = self.config.get("fixer_service_url")

        self.active_incidents: Dict[str, Dict] = {}
        self.is_running = False
        self.monitoring_interval = self.config.get("monitoring_interval", 30)

    def _default_config(self) -> Dict[str, Any]:
        return {
            "monitoring_interval": 30,
            "max_remediation_attempts": 3,
            "enable_auto_remediation": True,
            "alert_on_detection": True,
            "log_all_incidents": True,
            "services_to_monitor": ["all"],
            "detector_service_url": "http://localhost:8001",
            "rca_service_url": "http://localhost:8002",
            "fixer_service_url": "http://localhost:8003"
        }
    


    async def _collect_telemetry(self) -> Dict[str, Any]:

        try:
            metrics = await self.telemetry.get_metrics(
                services=self.config["services_to_monitor"],
                timeframe=f"{self.monitoring_interval}s"
            )

            telemetry_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics,
                "logs": [],
                "traces": []
            }

            print("\n[Telemetry] Mock metrics received:")
            print(metrics)

            return telemetry_data

        except Exception as e:
            print(f"[Telemetry] Error: {e}")
            return {"metrics": {}}   
        



    #MAIN ORCHESTRATION LOGIC
    async def start(self):
        print("[Orchestrator] Starting autonomous incident management system...")
        self.is_running = True
        await self._orchestration_loop()

    async def _orchestration_loop(self):
        while self.is_running:
            try:
                telemetry_data = await self._collect_telemetry()   # change it to real telemetry collection from datadog connector in future. For now we will use mock data for testing.
                detection_result = await self._run_detection(telemetry_data)

                if detection_result.get("action") == "alert":
                    await self._handle_incident(detection_result, telemetry_data)

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                print(f"[Orchestrator] Error in orchestration loop: {e}")
                await asyncio.sleep(self.monitoring_interval)





    # DETECTOR SERVICE CALL
    async def _run_detection(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            detector_state = telemetry_data.get("metrics", {})

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.detector_service_url}/detect",
                    json=detector_state,
                    timeout=10
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            print(f"[Orchestrator] Error calling detector service: {e}")
            return {"action": "error", "error": str(e)}





    # INCIDENT HANDLING
    async def _handle_incident(self, detection_result: Dict[str, Any], telemetry_data: Dict[str, Any]):

        incident_id =str(uuid.uuid4())

        print(f"\n[Orchestrator] INCIDENT DETECTED: {incident_id}")



        incident_record = {
            "incident_id":incident_id,
            "state" : IncidentState.ANOMALY_DETECTED.value,
            "detection_time":datetime.now(timezone.utc).isoformat(),
            "detection_result":detection_result,
            "telemetry_snapshot": telemetry_data,
            "timeline": []
        }

        self.active_incidents[incident_id]=incident_record

        params = cast(Dict[str,Any],detection_result.get("parameters", {}))
        severity = params.get("severity")

        if severity in ["HIGH","CRITICAL"]:
            await self._run_rca_pipeline(incident_id)
        else:
            await self._alert_only(incident_id)






    # RCA SERVICE CALL
    async def _run_rca_pipeline(self, incident_id: str):

        incident = self.active_incidents[incident_id]
        incident["state"] = IncidentState.RCA_IN_PROGRESS.value

        params = incident.get("detection_result", {}).get("parameters", {})

        rca_state = {
            "incident_id": incident_id,
            "anomalies": params.get("anomalies", []),
            "severity": params.get("severity"),
            "telemetry": incident.get("telemetry_snapshot"),
            "detection_time": incident.get("detection_time")
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                f"{self.rca_service_url}/analyze",
                json=rca_state,
                timeout=15
            )

                response.raise_for_status()
                rca_result = response.json()

            if "parameters" not in rca_result:
                raise ValueError("Invalid RCA response")

            incident["rca_result"] = rca_result

            incident["timeline"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "rca_completed",
                "details": rca_result
            })

            if self.config.get("enable_auto_remediation", True):
                await self._run_remediation(incident_id)
            else:
                await self._log_incident(incident_id)

        except Exception as e:
            print(f"[Orchestrator] RCA service error: {e}")
            incident["state"] = IncidentState.FAILED.value
            await self._log_incident(incident_id)









    # FIXER SERVICE CALL
    
    # async def _run_remediation(self, incident_id: str):

    #     incident = self.active_incidents[incident_id]
    #     incident["state"] = IncidentState.REMEDIATION_IN_PROGRESS.value

    #     max_attempts = self.config.get("max_remediation_attempts", 3)

    #     for attempt in range(1, max_attempts + 1):

    #         fixer_state = {
    #             "incident_id": incident_id,
    #             "root_cause": incident["rca_result"]["parameters"].get("root_cause"),
    #             "affected_services": incident["rca_result"]["parameters"].get("affected_services"),
    #             "recommended_fixes": incident["rca_result"]["parameters"].get("recommended_fixes"),
    #             "attempt": attempt
    #         }

    #         try:
    #             async with httpx.AsyncClient() as client:
    #                 response = await client.post(
    #                     f"{self.fixer_service_url}/remediate",
    #                     json=fixer_state,
    #                     timeout=20
    #                 )

    #                 response.raise_for_status()
    #                 fix_result = response.json()

    #             if await self._verify_remediation(incident_id):
    #                 incident["state"] = IncidentState.RESOLVED.value
    #                 await self._log_incident(incident_id)
    #                 del self.active_incidents[incident_id]
    #                 return

    #         except Exception as e:
    #             print(f"[Orchestrator] Fixer service error: {e}")

    #     incident["state"] = IncidentState.FAILED.value
    #     await self._log_incident(incident_id)








    # async def _verify_remediation(self, incident_id: str) -> bool:
    #     await asyncio.sleep(5)
    #     verification_telemetry = await self._collect_telemetry()
    #     verification_result = await self._run_detection(verification_telemetry)
    #     return verification_result.get("action") != "alert"



    async def _alert_only(self, incident_id: str):
        await self._log_incident(incident_id)
        del self.active_incidents[incident_id]



    async def _log_incident(self, incident_id: str):
        incident = self.active_incidents.get(incident_id)
        if incident:
            await self.logger.log_incident(incident)



    async def stop(self):
        self.is_running = False
        print("[Orchestrator] Stopping orchestration loop...")