import prisma from "../db/prisma";

export const recordAuditEvent = async (event: {
    incidentId: string;
    type: string;
    data: any;
}) => {
    await prisma.auditEvent.create({
        data: {
            incidentId: event.incidentId,
            type: event.type,
            data: event.data,
        },
    });
};

export const getIncidentAuditTrail = async (incidentId: string) => {
    return prisma.auditEvent.findMany({
        where: { incidentId },
        orderBy: { timestamp: "asc" },
    });
};
