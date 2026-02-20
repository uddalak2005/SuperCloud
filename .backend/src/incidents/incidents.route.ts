import { Router } from "express";
import prisma from "../db/prisma";

const router = Router();

router.get("/", async (req, res) => {
    const incidents = await prisma.incident.findMany({
        orderBy: { createdAt: "desc" },
    });

    res.json(incidents);
});

export default router;
