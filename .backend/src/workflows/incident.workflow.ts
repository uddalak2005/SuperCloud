import { NormalizedIncident } from "../ingestion/normaliser";
import { v4 as uuidv4 } from "uuid";
import { callAgent } from "../agents/agent.service";
import { evaluatePolicy } from "../policies/policy.engine";
import { executeAction } from "../execution/executor.service";
import { recordAuditEvent } from "../audit/audit.service";
import prisma from '../db/prisma';

export const runIncidentWorkflow = async (
    incident: NormalizedIncident
) => {
    const incidentId = uuidv4();

    // 1️⃣ Create incident
    await prisma.incident.create({
        data: {
            id: incidentId,
            source: incident.source,
            severity: incident.severity,
            service: incident.service,
            status: "OPEN",
        },
    });

    // 2️⃣ Audit: alert ingested
    await recordAuditEvent({
        incidentId,
        type: "ALERT_INGESTED",
        data: incident,
    });

    // 3️⃣ Choose agent
    let agentName = "IncidentResponseAgent";
    if (incident.signalType === "METRIC_ALERT") {
        agentName = "SelfHealingAgent";
    }

    // 4️⃣ Agent decision
    const agentResult = await callAgent(agentName as any, {
        incidentId,
        context: incident,
    });

    await recordAuditEvent({
        incidentId,
        type: "AGENT_DECISION",
        data: agentResult,
    });

    // 5️⃣ Policy evaluation
    const policyDecision = evaluatePolicy(
        agentResult.decision,
        incident.severity
    );

    await recordAuditEvent({
        incidentId,
        type: "POLICY_EVALUATION",
        data: policyDecision,
    });

    // 6️⃣ Blocked by policy
    if (!policyDecision.allowed) {
        await prisma.incident.update({
            where: { id: incidentId },
            data: { status: "BLOCKED" },
        });

        await recordAuditEvent({
            incidentId,
            type: "INCIDENT_BLOCKED",
            data: { reason: policyDecision.reason },
        });

        return {
            incidentId,
            status: "BLOCKED_BY_POLICY",
            reason: policyDecision.reason,
        };
    }

    // 7️⃣ Execute action
    const executionResult = await executeAction(
        agentResult.decision,
        incident.service
    );

    await recordAuditEvent({
        incidentId,
        type: "ACTION_EXECUTED",
        data: executionResult,
    });

    // 8️⃣ Persist execution
    await prisma.execution.create({
        data: {
            incidentId,
            action: agentResult.decision,
            success: executionResult.success,
            message: executionResult.message,
        },
    });

    // 9️⃣ Mark incident resolved
    await prisma.incident.update({
        where: { id: incidentId },
        data: { status: "RESOLVED" },
    });

    await recordAuditEvent({
        incidentId,
        type: "INCIDENT_RESOLVED",
        data: { success: executionResult.success },
    });

    return {
        incidentId,
        status: "RESOLVED",
        decision: agentResult.decision,
        execution: executionResult.message,
    };
};
