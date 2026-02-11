import asyncio
import sys
from pathlib import Path

from orchestrator import Orchestrator
from telemetry_connector import DatadogConnector, CompositeConnector, PrometheusConnector, LokiConnector
#from incident_logger import IncidentLogger
#from fixer_agent import FixerAgent


async def main():
    """
    Initialize and run the autonomous incident management system
    """
    print("Autonomous Incident Management System")

    #Initialize Telemetry Connector
    
    
    print("[Setup] Initializing telemetry connector...")
    
    # Option A: Single connecto
    telemetry = DatadogConnector({
        "api_key": "DATADOG_API_KEY",
        "app_key": "DATADOG_APP_KEY",
        "site": "datadoghq.com"
    })  #right now we are using mock telemetry data for testing.
    
    # Option B: Composite connector (Prometheus + Loki + Tempo)
    # composite = CompositeConnector({})
    # composite.add_connector("prometheus", PrometheusConnector({
    #     "url": "http://localhost:9090"
    # }))
    # composite.add_connector("loki", LokiConnector({
    #     "url": "http://localhost:3100"
    # }))
    # telemetry = composite
    
    # Connect to telemetry system
    await telemetry.connect()
    
   




    #Initialize Agents
    print("[Setup] Initializing agents...")
    
    print("[Setup] Connnecting with external agent services...")

    detector = "http://localhost:8001"

    # Configure baseline metrics for anomaly detection
    # In production, these would be learned from historical data
    detector.baseline_metrics = {
        "cpu_usage_percent": {"mean": 45.0, "std": 15.0},
        "memory_usage_percent": {"mean": 60.0, "std": 10.0},
        "response_time_ms": {"mean": 150.0, "std": 50.0},
        "error_rate_percent": {"mean": 0.5, "std": 0.3},
        "http_request_rate": {"mean": 250.0, "std": 50.0}
    }
    
    # RCA Brain Agent
    rca_brain = "http://localhost:8002"
    
    # Fixer Agent
    # fixer = FixerAgent(
    #     agent_id="fixer-001",
    #     rulebook_path="rulebook.json"  # Will use default if not found
    # )
   
    #Initialize Incident Logger
    
    print("[Setup] Initializing incident logger...")
    
    #incident_logger = IncidentLogger(db_path="incidents.db")
    
    #Initialize Orchestrator

    
    print("[Setup] Initializing orchestrator...")
    
    orchestrator_config = {
        "monitoring_interval": 30, 
        "max_remediation_attempts": 3,
        "enable_auto_remediation": True,
        "alert_on_detection": True,
        "log_all_incidents": True,
        "services_to_monitor": ["all"],
        "collect_logs": True,
        "collect_traces": False
    }
    
    orchestrator = Orchestrator(
        telemetry_connector=telemetry,
        detector_agent=detector,
        rca_agent=rca_brain,
        #fixer_agent=fixer,
        #incident_logger=incident_logger,
        config=orchestrator_config
    )
    

    # STEP 5: Start Orchestration Loop
   
    
    print()
    print("[Setup] All components initialized")
    print()
    
    print("Starting autonomous monitoring and remediation...")
    print("Press Ctrl+C to stop")
   
    print()
    
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")
        await orchestrator.stop()
        #incident_logger.close()
        await telemetry.disconnect()
        print("[Main]  Shutdown complete")
    except Exception as e:
        print(f"[Main]  Fatal error: {e}")
        await orchestrator.stop()
        #incident_logger.close()
        await telemetry.disconnect()



#historical incident analytics using incident logger, we will use ML Models to analyze historical incidents and identify patterns, common root causes, and effective remediation strategies. This can help us continuously improve our incident management system and make it more proactive over time.

# def run_analytics():
#     """
#     Analyze historical incidents for pattern recognition
#     """
 
#     print(" Incident Analytics")
   
#     print()
    
#     logger = IncidentLogger(db_path="incidents.db")
    
#     # Get statistics
#     stats = logger.get_statistics()
    
#     print(f"Total Incidents: {stats.get('total_incidents', 0)}")
#     print(f"Resolved: {stats.get('resolved', 0)}")
#     print(f"Failed: {stats.get('failed', 0)}")
#     print(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
#     print(f"Avg Remediation Attempts: {stats.get('avg_remediation_attempts', 0)}")
#     print()
    
#     print("By Severity:")
#     for severity, count in stats.get('by_severity', {}).items():
#         print(f"  {severity}: {count}")
#     print()
    
#     print("Most Common Root Causes:")
#     for cause in stats.get('common_root_causes', []):
#         print(f"  - {cause['root_cause']}: {cause['count']} incidents")
#     print()
    
#     # Get recent incidents
#     print("Recent Incidents:")
#     recent = logger.get_recent_incidents(limit=5)
#     for inc in recent:
#         status = "SUCCESS" if inc['success'] else "FAILED"
#         print(f"  {status} [{inc['severity']}] {inc['incident_id'][:8]}... - {inc['root_cause']}")
    
#     logger.close()


# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1 and sys.argv[1] == "analytics":
#         # Run analytics mode
#         run_analytics()
#     else:
#         # Run orchestrator
#         asyncio.run(main())