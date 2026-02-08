import express from 'express';
import { errorHandler } from './middleware/errorHandler';
import ingestionRoute from "./ingestion/ingestion.route"
import auditRoutes from "./audit/audit.routes";


const app = express();

app.use(express.json());

//Routes
app.use("/ingest", ingestionRoute);
app.use("/audit", auditRoutes);


//Global Error Handler
app.use(errorHandler);

export default app;