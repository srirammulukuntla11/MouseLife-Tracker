import { mouseService } from "../services/mouseService.js";

export const syncClicks = async (req, res, next) => {
  try {
    const { batchId, mouseId, clientSessionId, leftClicks, rightClicks, middleClicks, totalClicks, timestamp } = req.body;

    if (!batchId) {
      return res.status(400).json({
        success: false,
        message: "Validation Error: batchId is required for duplicate-safe synchronization",
      });
    }

    const result = await mouseService.processSyncBatch({
      batchId,
      mouseId: mouseId || "portronics-default-01",
      clientSessionId,
      leftClicks,
      rightClicks,
      middleClicks,
      totalClicks,
      timestamp,
    });

    res.status(200).json({
      success: true,
      ...result,
    });
  } catch (err) {
    next(err);
  }
};
