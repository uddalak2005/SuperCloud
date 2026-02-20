import {Router} from "express";
import ingestionController from "./ingestion.controller";

const router =Router();

router.post("/alert", ingestionController.ingestAlert);

export default router;