import express from 'express';
import { errorHandler } from './middleware/errorHandler';
import ingestionRoute from "./ingestion/ingestion.route"
import auditRoutes from "./audit/audit.route";
import incidentsRoutes from "./incidents/incidents.route";


const app = express();

app.use(express.json());

//Routes
app.use("/ingest", ingestionRoute);
app.use("/audit", auditRoutes);
app.use("/incidents", incidentsRoutes);


//Global Error Handler
app.use(errorHandler);

export default app;