export type AuditEventType =
    | "ALERT_INGESTED"
    | "AGENT_DECISION"
    | "POLICY_EVALUATION"
    | "ACTION_EXECUTED"
    | "INCIDENT_RESOLVED"
    | "INCIDENT_BLOCKED";

export interface AuditEvent {
    incidentId: string;
    type: AuditEventType;
    timestamp: string;
    data: any;
}
