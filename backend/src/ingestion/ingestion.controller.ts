import {Request, Response, NextFunction} from "express";
import {normalizeAlert} from "./normaliser";
import { runIncidentWorkflow } from "../workflows/incident.workflow";

class IngestionController {
    async ingestAlert(req: Request, res : Response, next : NextFunction) : Promise<void> {
        try{
            const rawAlert = req.body;

            const normalizedIncident = normalizeAlert(rawAlert);

            const workflowResult = await runIncidentWorkflow(normalizedIncident);

            res.status(201).json({
                status: "WORKFLOW_STARTED",
                incident: normalizedIncident,
                workflow: workflowResult,
            })

        }catch(err){
            next(err);
        }
    }
}

export default new IngestionController();