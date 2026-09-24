import express from "express";
import {
  getHealth,
  getAllMice,
  getMouseById,
  createMouse,
  updateMouse,
  getDailyStatistics,
  getWeeklyStatistics,
  getMonthlyStatistics,
  getSessions,
} from "../controllers/mouseController.js";
import { syncClicks } from "../controllers/syncController.js";
import { startSession, endSession } from "../controllers/sessionController.js";

const router = express.Router();

// Health
router.get("/health", getHealth);

// Mice Management
router.get("/mice", getAllMice);
router.post("/mice", createMouse);
router.get("/mice/:id", getMouseById);
router.patch("/mice/:id", updateMouse);

// Click Synchronization
router.post("/clicks/sync", syncClicks);

// Statistics Analytics
router.get("/mice/:id/statistics/daily", getDailyStatistics);
router.get("/mice/:id/statistics/weekly", getWeeklyStatistics);
router.get("/mice/:id/statistics/monthly", getMonthlyStatistics);

// Session Tracking
router.get("/mice/:id/sessions", getSessions);
router.post("/sessions/start", startSession);
router.post("/sessions/end", endSession);

export default router;
