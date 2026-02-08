import { AuditEvent } from "./audit.types";

const auditStore: AuditEvent[] = [];

export const recordAuditEvent = (
    event: AuditEvent
) => {
    auditStore.push(event);
};

export const getIncidentAuditTrail = (
    incidentId: string
): AuditEvent[] => {
    return auditStore.filter(
        (event) => event.incidentId === incidentId
    );
};
