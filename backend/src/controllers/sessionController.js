import { mouseService } from "../services/mouseService.js";

export const startSession = async (req, res, next) => {
  try {
    const { sessionId, mouseId, startedAt } = req.body;
    if (!sessionId) {
      return res.status(400).json({ success: false, message: "sessionId is required" });
    }

    const session = await mouseService.startSession({
      sessionId,
      mouseId: mouseId || "portronics-default-01",
      startedAt,
    });

    res.status(201).json({ success: true, data: session });
  } catch (err) {
    next(err);
  }
};

export const endSession = async (req, res, next) => {
  try {
    const { sessionId, endedAt, duration, totalClicks, leftClicks, rightClicks, middleClicks } = req.body;
    if (!sessionId) {
      return res.status(400).json({ success: false, message: "sessionId is required" });
    }

    const session = await mouseService.endSession({
      sessionId,
      endedAt,
      duration,
      totalClicks,
      leftClicks,
      rightClicks,
      middleClicks,
    });

    res.status(200).json({ success: true, data: session });
  } catch (err) {
    next(err);
  }
};
