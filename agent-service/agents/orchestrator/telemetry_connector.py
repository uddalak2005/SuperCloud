from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone




class TelemetryConnector(ABC):
    """
    Abstract base class for telemetry connectors
    Implementations: DatadogConnector, PrometheusConnector, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connector with configuration
        
        Args:
            config: Connector-specific configuration
        """
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to telemetry system
        Returns: True if successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to telemetry system"""
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch metrics from telemetry system
        
        Args:
            services: List of service names to monitor (or ["all"])
            timeframe: Time window (e.g., "30s", "5m", "1h")
            metric_types: Optional list of specific metrics to fetch
            
        Returns:
            Dict of metric_name: value
        """
        pass
    
    @abstractmethod
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from telemetry system
        
        Args:
            services: List of service names
            timeframe: Time window
            log_level: Optional filter (ERROR, WARN, INFO, etc.)
            
        Returns:
            List of log entries
        """
        pass
    
    @abstractmethod
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """
        Fetch distributed traces
        
        Args:
            services: List of service names
            timeframe: Time window
            
        Returns:
            List of trace data
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of telemetry connection
        
        Returns:
            Dict with status and connection info
        """
        return {
            "connected": self.is_connected,
            "connector_type": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat()
        }











#DATADOG CONNECTOR IMPLEMENTATION


class DatadogConnector(TelemetryConnector):
    """
    Datadog telemetry connector implementation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Datadog connector
        
        Config should include:
        - api_key: Datadog API key
        - app_key: Datadog application key
        - site: Datadog site (e.g., 'datadoghq.com')
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.app_key = config.get("app_key")
        self.site = config.get("site", "datadoghq.com")
        self.client = None
    
    async def connect(self) -> bool:
        """Establish connection to Datadog"""
        try:
            # TODO: Initialize Datadog API client
            # from datadog_api_client import ApiClient, Configuration
            # configuration = Configuration()
            # configuration.api_key["apiKeyAuth"] = self.api_key
            # configuration.api_key["appKeyAuth"] = self.app_key
            # self.client = ApiClient(configuration)
            
            self.is_connected = True
            print(f"[DatadogConnector] Connected to Datadog ({self.site})")
            return True
            
        except Exception as e:
            print(f"[DatadogConnector] Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Datadog"""
        self.is_connected = False
        self.client = None
        print(f"[DatadogConnector] Disconnected")
    
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch metrics from Datadog
        
        Example metrics:
        - system.cpu.usage
        - system.mem.used
        - system.disk.io
        - http.request.duration
        - error.rate
        """
        try:
            # TODO: Implement actual Datadog API call
            # from datadog_api_client.v1.api.metrics_api import MetricsApi
            # api_instance = MetricsApi(self.client)
            # 
            # now = int(datetime.now().timestamp())
            # from_time = now - self._parse_timeframe(timeframe)
            # 
            # query = "avg:system.cpu.usage{*}"
            # response = api_instance.query_metrics(from_time, now, query)
            
            # PLACEHOLDER: Return mock metrics for testing
            return self._get_mock_metrics(services, timeframe)
            
        except Exception as e:
            print(f"[DatadogConnector] Error fetching metrics: {e}")
            return {}
    
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch logs from Datadog"""
        try:
            # TODO: Implement Datadog logs API
            # from datadog_api_client.v2.api.logs_api import LogsApi
            
            # PLACEHOLDER
            return []
            
        except Exception as e:
            print(f"[DatadogConnector] Error fetching logs: {e}")
            return []
    
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """Fetch traces from Datadog APM"""
        try:
            # TODO: Implement Datadog APM API
            
            # PLACEHOLDER
            return []
            
        except Exception as e:
            print(f"[DatadogConnector] Error fetching traces: {e}")
            return []
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to seconds"""
        import re
        match = re.match(r'(\d+)([smhd])', timeframe)
        if not match:
            return 30
        
        value, unit = int(match.group(1)), match.group(2)
        multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        return value * multipliers.get(unit, 1)
    
    def _get_mock_metrics(self, services: List[str], timeframe: str) -> Dict[str, Any]:
        """Generate mock metrics for testing (REMOVE IN PRODUCTION)"""
        import random
        
        return {
            "cpu_usage_percent": random.uniform(20, 95),
            "memory_usage_percent": random.uniform(30, 85),
            "disk_io_ops": random.uniform(100, 1000),
            "network_throughput_mbps": random.uniform(10, 100),
            "http_request_rate": random.uniform(50, 500),
            "error_rate_percent": random.uniform(0, 5),
            "response_time_ms": random.uniform(50, 500),
            "db_connection_pool": random.randint(10, 100)
        }












# Placeholder implementations for other connectors (Prometheus, Loki, Tempo) can be added similarly, following the TelemetryConnector interface.




class PrometheusConnector(TelemetryConnector):
    """
    Prometheus telemetry connector implementation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Prometheus connector
        
        Config should include:
        - url: Prometheus server URL
        - timeout: Query timeout
        """
        super().__init__(config)
        self.url = config.get("url", "http://localhost:9090")
        self.timeout = config.get("timeout", 30)
    
    async def connect(self) -> bool:
        """Establish connection to Prometheus"""
        try:
            # TODO: Verify Prometheus connectivity
            # import aiohttp
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(f"{self.url}/-/healthy", timeout=self.timeout) as resp:
            #         if resp.status == 200:
            #             self.is_connected = True
            
            self.is_connected = True
            print(f"[PrometheusConnector] Connected to Prometheus ({self.url})")
            return True
            
        except Exception as e:
            print(f"[PrometheusConnector] Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Prometheus"""
        self.is_connected = False
        print(f"[PrometheusConnector] Disconnected")
    
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch metrics from Prometheus using PromQL
        """
        try:
            # TODO: Implement Prometheus query API
            # import aiohttp
            # 
            # queries = {
            #     "cpu_usage": 'rate(node_cpu_seconds_total{mode!="idle"}[5m])',
            #     "memory_usage": 'node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes',
            # }
            # 
            # async with aiohttp.ClientSession() as session:
            #     for metric, query in queries.items():
            #         async with session.get(
            #             f"{self.url}/api/v1/query",
            #             params={"query": query}
            #         ) as resp:
            #             data = await resp.json()
            
            # PLACEHOLDER
            return {}
            
        except Exception as e:
            print(f"[PrometheusConnector] Error fetching metrics: {e}")
            return {}
    
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Prometheus doesn't handle logs - use Loki instead"""
        print(f"[PrometheusConnector] Prometheus doesn't support logs. Use LokiConnector.")
        return []
    
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """Prometheus doesn't handle traces - use Tempo instead"""
        print(f"[PrometheusConnector] Prometheus doesn't support traces. Use TempoConnector.")
        return []


class LokiConnector(TelemetryConnector):
    """
    Grafana Loki log aggregation connector
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:3100")
    
    async def connect(self) -> bool:
        """Connect to Loki"""
        try:
            self.is_connected = True
            print(f"[LokiConnector] Connected to Loki ({self.url})")
            return True
        except Exception as e:
            print(f"[LokiConnector] Connection failed: {e}")
            return False
    
    async def disconnect(self):
        self.is_connected = False
        print(f"[LokiConnector] Disconnected")
    
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Loki is for logs, not metrics"""
        return {}
    
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from Loki using LogQL
        """
        try:
            # TODO: Implement Loki query API
            # query = '{job="service"} |= "error"'
            # params = {
            #     "query": query,
            #     "limit": 100,
            #     "start": start_time,
            #     "end": end_time
            # }
            
            # PLACEHOLDER
            return []
            
        except Exception as e:
            print(f"[LokiConnector] Error fetching logs: {e}")
            return []
    
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """Loki doesn't handle traces"""
        return []


class TempoConnector(TelemetryConnector):
    """
    Grafana Tempo distributed tracing connector
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:3200")
    
    async def connect(self) -> bool:
        """Connect to Tempo"""
        try:
            self.is_connected = True
            print(f"[TempoConnector] Connected to Tempo ({self.url})")
            return True
        except Exception as e:
            print(f"[TempoConnector] Connection failed: {e}")
            return False
    
    async def disconnect(self):
        self.is_connected = False
        print(f"[TempoConnector] Disconnected")
    
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Tempo is for traces, not metrics"""
        return {}
    
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Tempo doesn't handle logs"""
        return []
    
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """
        Fetch distributed traces from Tempo
        """
        try:
            # TODO: Implement Tempo API
            # GET /api/traces/{traceId}
            # GET /api/search
            
            # PLACEHOLDER
            return []
            
        except Exception as e:
            print(f"[TempoConnector] Error fetching traces: {e}")
            return []


class CompositeConnector(TelemetryConnector):
    """
    Composite connector that aggregates multiple telemetry sources
    Example: Prometheus (metrics) + Loki (logs) + Tempo (traces)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connectors: Dict[str, TelemetryConnector] = {}
    
    def add_connector(self, name: str, connector: TelemetryConnector):
        """Add a telemetry connector to the composite"""
        self.connectors[name] = connector
    
    async def connect(self) -> bool:
        """Connect all connectors"""
        results = []
        for name, connector in self.connectors.items():
            result = await connector.connect()
            results.append(result)
            if result:
                print(f"[CompositeConnector] {name} connected")
        
        self.is_connected = all(results)
        return self.is_connected
    
    async def disconnect(self):
        """Disconnect all connectors"""
        for connector in self.connectors.values():
            await connector.disconnect()
        self.is_connected = False
    
    async def get_metrics(
        self,
        services: List[str],
        timeframe: str = "30s",
        metric_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Aggregate metrics from all metric-capable connectors"""
        all_metrics = {}
        for connector in self.connectors.values():
            metrics = await connector.get_metrics(services, timeframe, metric_types)
            all_metrics.update(metrics)
        return all_metrics
    
    async def get_logs(
        self,
        services: List[str],
        timeframe: str = "30s",
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate logs from all log-capable connectors"""
        all_logs = []
        for connector in self.connectors.values():
            logs = await connector.get_logs(services, timeframe, log_level)
            all_logs.extend(logs)
        return all_logs
    
    async def get_traces(
        self,
        services: List[str],
        timeframe: str = "30s"
    ) -> List[Dict[str, Any]]:
        """Aggregate traces from all trace-capable connectors"""
        all_traces = []
        for connector in self.connectors.values():
            traces = await connector.get_traces(services, timeframe)
            all_traces.extend(traces)
        return all_traces