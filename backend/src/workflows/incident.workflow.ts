import { NormalizedIncident } from "../ingestion/normaliser";
import { v4 as uuidv4 } from "uuid";
import { callAgent } from "../agents/agent.service";
import { evaluatePolicy } from "../policies/policy.engine";
import { executeAction } from "../execution/executor.service";
import { recordAuditEvent } from "../audit/audit.service";

export const runIncidentWorkflow = async (
    incident: NormalizedIncident
) => {
    const incidentId = uuidv4();

    // 🔹 Audit: Alert ingested
    recordAuditEvent({
        incidentId,
        type: "ALERT_INGESTED",
        timestamp: new Date().toISOString(),
        data: incident,
    });

    let agentName = "IncidentResponseAgent";

    if (incident.signalType === "METRIC_ALERT") {
        agentName = "SelfHealingAgent";
    }

    // 🔹 Agent decision
    const agentResult = await callAgent(agentName as any, {
        incidentId,
        context: incident,
    });

    recordAuditEvent({
        incidentId,
        type: "AGENT_DECISION",
        timestamp: new Date().toISOString(),
        data: agentResult,
    });

    // 🔹 Policy evaluation
    const policyDecision = evaluatePolicy(
        agentResult.decision,
        incident.severity
    );

    recordAuditEvent({
        incidentId,
        type: "POLICY_EVALUATION",
        timestamp: new Date().toISOString(),
        data: policyDecision,
    });

    if (!policyDecision.allowed) {
        recordAuditEvent({
            incidentId,
            type: "INCIDENT_BLOCKED",
            timestamp: new Date().toISOString(),
            data: { reason: policyDecision.reason },
        });

        return {
            incidentId,
            status: "BLOCKED_BY_POLICY",
            reason: policyDecision.reason,
        };
    }

    // 🔹 Execute action
    const executionResult = await executeAction(
        agentResult.decision,
        incident.service
    );

    recordAuditEvent({
        incidentId,
        type: "ACTION_EXECUTED",
        timestamp: new Date().toISOString(),
        data: executionResult,
    });

    recordAuditEvent({
        incidentId,
        type: "INCIDENT_RESOLVED",
        timestamp: new Date().toISOString(),
        data: { success: executionResult.success },
    });

    return {
        incidentId,
        status: "RESOLVED",
        decision: agentResult.decision,
        execution: executionResult.message,
    };
};
