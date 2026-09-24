import { Mouse } from "../models/Mouse.js";
import { DailyStatistic } from "../models/DailyStatistic.js";
import { ClickSession } from "../models/ClickSession.js";
import { SyncBatch } from "../models/SyncBatch.js";

export const mouseService = {
  /**
   * Ensures a mouse profile exists, creating default Portronics mouse if absent.
   */
  async ensureMouse(mouseId = "portronics-default-01", customData = {}) {
    let mouse = await Mouse.findOne({ mouseId });
    if (!mouse) {
      mouse = await Mouse.create({
        mouseId,
        name: customData.name || "Portronics Wireless Mouse",
        manufacturer: customData.manufacturer || "Portronics",
        model: customData.model || "Toad 23 / Wireless Optical",
        ratedClicks: customData.ratedClicks || 3000000,
        totalClicks: 0,
        leftClicks: 0,
        rightClicks: 0,
        middleClicks: 0,
        trackingStartedAt: new Date(),
      });
      console.log(`[MouseService] Initialized default profile for mouseId: ${mouseId}`);
    }
    return mouse;
  },

  /**
   * Retrieves all mice.
   */
  async getAllMice() {
    return await Mouse.find().sort({ createdAt: -1 });
  },

  /**
   * Retrieves a single mouse by mouseId.
   */
  async getMouseById(mouseId) {
    let mouse = await Mouse.findOne({ mouseId });
    if (!mouse && mouseId === "portronics-default-01") {
      mouse = await this.ensureMouse(mouseId);
    }
    return mouse;
  },

  /**
   * Updates metadata or rated clicks for a mouse.
   */
  async updateMouse(mouseId, updateData) {
    const allowed = ["name", "manufacturer", "model", "ratedClicks"];
    const sanitized = {};
    for (const key of allowed) {
      if (updateData[key] !== undefined) sanitized[key] = updateData[key];
    }

    return await Mouse.findOneAndUpdate(
      { mouseId },
      { $set: sanitized },
      { new: true, runValidators: true }
    );
  },

  /**
   * Idempotent batch synchronization with duplicate detection and atomic increments.
   */
  async processSyncBatch(payload) {
    const {
      batchId,
      mouseId = "portronics-default-01",
      clientSessionId,
      leftClicks = 0,
      rightClicks = 0,
      middleClicks = 0,
      totalClicks = 0,
      timestamp,
    } = payload;

    if (!batchId) {
      throw new Error("Missing required batchId for synchronization");
    }

    // Ensure mouse exists
    await this.ensureMouse(mouseId);

    // 1. Idempotency Check: Has this batchId already been processed?
    const existingBatch = await SyncBatch.findOne({ batchId });
    if (existingBatch) {
      console.warn(`[MouseService] Duplicate sync request detected for batchId ${batchId}. Returning existing state without re-counting.`);
      const currentMouse = await Mouse.findOne({ mouseId });
      return {
        duplicate: true,
        message: "Batch already processed (idempotent acknowledgement)",
        batchId,
        mouse: currentMouse,
      };
    }

    // 2. Validate click amounts
    const safeLeft = Math.max(Number(leftClicks) || 0, 0);
    const safeRight = Math.max(Number(rightClicks) || 0, 0);
    const safeMiddle = Math.max(Number(middleClicks) || 0, 0);
    const safeTotal = safeLeft + safeRight + safeMiddle;

    // 3. Record the batch in MongoDB for audit and duplicate prevention
    await SyncBatch.create({
      batchId,
      mouseId,
      clientSessionId,
      leftClicks: safeLeft,
      rightClicks: safeRight,
      middleClicks: safeMiddle,
      totalClicks: safeTotal,
      clientTimestamp: timestamp || new Date().toISOString(),
      syncedAt: new Date(),
    });

    // 4. Atomically increment lifetime counters on Mouse document
    const updatedMouse = await Mouse.findOneAndUpdate(
      { mouseId },
      {
        $inc: {
          totalClicks: safeTotal,
          leftClicks: safeLeft,
          rightClicks: safeRight,
          middleClicks: safeMiddle,
        },
        $set: { lastSyncedAt: new Date() },
      },
      { new: true }
    );

    // 5. Atomically upsert DailyStatistic for today (YYYY-MM-DD)
    const todayDate = new Date().toISOString().split("T")[0];
    const dailyStat = await DailyStatistic.findOneAndUpdate(
      { mouseId, date: todayDate },
      {
        $inc: {
          totalClicks: safeTotal,
          leftClicks: safeLeft,
          rightClicks: safeRight,
          middleClicks: safeMiddle,
        },
      },
      { new: true, upsert: true }
    );

    // 6. Update session clicks if sessionId is provided
    if (clientSessionId) {
      await ClickSession.findOneAndUpdate(
        { sessionId: clientSessionId },
        {
          $inc: {
            totalClicks: safeTotal,
            leftClicks: safeLeft,
            rightClicks: safeRight,
            middleClicks: safeMiddle,
          },
        }
      );
    }

    return {
      duplicate: false,
      batchId,
      mouse: updatedMouse,
      dailyStatistic: dailyStat,
    };
  },

  /**
   * Retrieves daily statistics for a mouse (default last 30 days).
   */
  async getDailyStats(mouseId, days = 30) {
    const stats = await DailyStatistic.find({ mouseId })
      .sort({ date: -1 })
      .limit(days);
    return stats.reverse();
  },

  /**
   * Aggregates weekly statistics.
   */
  async getWeeklyStats(mouseId) {
    // Return last 8 weeks aggregated from daily statistics
    const daily = await DailyStatistic.find({ mouseId }).sort({ date: 1 });
    const weeksMap = new Map();

    for (const d of daily) {
      const dateObj = new Date(d.date);
      // Group by year and ISO week
      const year = dateObj.getFullYear();
      const weekNumber = Math.ceil(
        ((dateObj - new Date(year, 0, 1)) / 86400000 + new Date(year, 0, 1).getDay() + 1) / 7
      );
      const key = `${year}-W${String(weekNumber).padStart(2, "0")}`;

      if (!weeksMap.has(key)) {
        weeksMap.set(key, { week: key, totalClicks: 0, leftClicks: 0, rightClicks: 0, middleClicks: 0 });
      }
      const entry = weeksMap.get(key);
      entry.totalClicks += d.totalClicks;
      entry.leftClicks += d.leftClicks;
      entry.rightClicks += d.rightClicks;
      entry.middleClicks += d.middleClicks;
    }

    return Array.from(weeksMap.values()).slice(-8);
  },

  /**
   * Aggregates monthly statistics.
   */
  async getMonthlyStats(mouseId) {
    const daily = await DailyStatistic.find({ mouseId }).sort({ date: 1 });
    const monthsMap = new Map();

    for (const d of daily) {
      const monthKey = d.date.substring(0, 7); // "YYYY-MM"
      if (!monthsMap.has(monthKey)) {
        monthsMap.set(monthKey, { month: monthKey, totalClicks: 0, leftClicks: 0, rightClicks: 0, middleClicks: 0 });
      }
      const entry = monthsMap.get(monthKey);
      entry.totalClicks += d.totalClicks;
      entry.leftClicks += d.leftClicks;
      entry.rightClicks += d.rightClicks;
      entry.middleClicks += d.middleClicks;
    }

    return Array.from(monthsMap.values()).slice(-12);
  },

  /**
   * Retrieves tracking sessions for a mouse.
   */
  async getSessions(mouseId, limit = 20) {
    return await ClickSession.find({ mouseId }).sort({ startedAt: -1 }).limit(limit);
  },

  /**
   * Starts a new tracking session.
   */
  async startSession(sessionData) {
    const { sessionId, mouseId = "portronics-default-01", startedAt } = sessionData;
    await this.ensureMouse(mouseId);

    return await ClickSession.findOneAndUpdate(
      { sessionId },
      {
        $setOnInsert: {
          sessionId,
          mouseId,
          startedAt: startedAt ? new Date(startedAt) : new Date(),
          totalClicks: 0,
          leftClicks: 0,
          rightClicks: 0,
          middleClicks: 0,
        },
      },
      { new: true, upsert: true }
    );
  },

  /**
   * Finalizes an active tracking session.
   */
  async endSession(sessionData) {
    const { sessionId, endedAt, duration, totalClicks, leftClicks, rightClicks, middleClicks } = sessionData;
    const end = endedAt ? new Date(endedAt) : new Date();

    const existing = await ClickSession.findOne({ sessionId });
    let calculatedDuration = duration;
    if (!calculatedDuration && existing) {
      calculatedDuration = Math.max((end.getTime() - new Date(existing.startedAt).getTime()) / 1000, 0);
    }

    return await ClickSession.findOneAndUpdate(
      { sessionId },
      {
        $set: {
          endedAt: end,
          duration: calculatedDuration || 0,
          ...(totalClicks !== undefined && { totalClicks }),
          ...(leftClicks !== undefined && { leftClicks }),
          ...(rightClicks !== undefined && { rightClicks }),
          ...(middleClicks !== undefined && { middleClicks }),
        },
      },
      { new: true, upsert: true }
    );
  },
};
