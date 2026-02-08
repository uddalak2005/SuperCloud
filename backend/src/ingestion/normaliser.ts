export interface NormalizedIncident{
    source : "PROMETHEUS" | "LOKI" | "TEMPO" | "GRAFANA";
    signalType : "METRIC_ALERT" | "LOG_ALERT" | "TRACE_ALERT" | "CORRELATED_ALERT";
    severity : "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    service : string;
    summary : string;
    raw : any;
    timestamp : string;
}

export function normalizeAlert(alert : any) : NormalizedIncident{
    if (!alert || !alert.source) {
        throw new Error("Alert source missing");
    }

    switch (alert.source) {
        case "PROMETHEUS":
            return normalizePrometheus(alert);

        case "LOKI":
            return normalizeLoki(alert);

        case "TEMPO":
            return normalizeTempo(alert);

        case "GRAFANA":
            return normalizeGrafana(alert);

        default:
            throw new Error(`Unsupported alert source: ${alert.source}`);
    }
}

const normalizePrometheus = (alert: any): NormalizedIncident => {
    return {
        source: "PROMETHEUS",
        signalType: "METRIC_ALERT",
        severity: mapSeverity(alert.severity),
        service: alert.resource?.name || "unknown-service",
        summary: alert.alertName || "Prometheus metric alert",
        raw: alert,
        timestamp: alert.timestamp || new Date().toISOString(),
    };
};


const normalizeLoki = (alert: any): NormalizedIncident => {
    return {
        source: "LOKI",
        signalType: "LOG_ALERT",
        severity: mapSeverity(alert.severity),
        service: alert.resource?.name || "unknown-service",
        summary: "Log anomaly detected",
        raw: alert,
        timestamp: alert.timestamp || new Date().toISOString(),
    };
};

const normalizeTempo = (alert: any): NormalizedIncident => {
    return {
        source: "TEMPO",
        signalType: "TRACE_ALERT",
        severity: mapSeverity(alert.severity),
        service: alert.trace?.service || "unknown-service",
        summary: "Trace latency anomaly detected",
        raw: alert,
        timestamp: alert.timestamp || new Date().toISOString(),
    };
};

const normalizeGrafana = (alert: any): NormalizedIncident => {
    return {
        source: "GRAFANA",
        signalType: "CORRELATED_ALERT",
        severity: mapSeverity(alert.severity),
        service: alert.affectedService || "unknown-service",
        summary: "Correlated multi-signal alert",
        raw: alert,
        timestamp: alert.timestamp || new Date().toISOString(),
    };
};


const mapSeverity = (severity: string): NormalizedIncident["severity"] => {
    switch (severity?.toUpperCase()) {
        case "CRITICAL":
            return "CRITICAL";
        case "HIGH":
            return "HIGH";
        case "MEDIUM":
            return "MEDIUM";
        default:
            return "LOW";
    }
};
