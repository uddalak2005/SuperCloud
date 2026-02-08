import express from "express";
import { getIncidentAuditTrail } from "./audit.service";

const router = express.Router();

router.get("/:incidentId", (req, res) => {
    const { incidentId } = req.params;
    const trail = getIncidentAuditTrail(incidentId);

    res.json({
        incidentId,
        events: trail,
    });
});

export default router;
