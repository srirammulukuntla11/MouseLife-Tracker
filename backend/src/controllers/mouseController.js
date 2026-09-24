import { mouseService } from "../services/mouseService.js";

export const getHealth = async (req, res) => {
  res.json({
    status: "ok",
    service: "MouseLife Tracker API",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
};

export const getAllMice = async (req, res, next) => {
  try {
    const mice = await mouseService.getAllMice();
    res.json({ success: true, count: mice.length, data: mice });
  } catch (err) {
    next(err);
  }
};

export const getMouseById = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const mouse = await mouseService.getMouseById(mouseId);
    if (!mouse) {
      return res.status(404).json({ success: false, message: `Mouse with ID '${mouseId}' not found.` });
    }
    res.json({ success: true, data: mouse });
  } catch (err) {
    next(err);
  }
};

export const createMouse = async (req, res, next) => {
  try {
    const { mouseId, name, manufacturer, model, ratedClicks } = req.body;
    if (!mouseId) {
      return res.status(400).json({ success: false, message: "mouseId is required" });
    }
    const mouse = await mouseService.ensureMouse(mouseId, {
      name,
      manufacturer,
      model,
      ratedClicks,
    });
    res.status(201).json({ success: true, data: mouse });
  } catch (err) {
    next(err);
  }
};

export const updateMouse = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const updated = await mouseService.updateMouse(mouseId, req.body);
    if (!updated) {
      return res.status(404).json({ success: false, message: `Mouse '${mouseId}' not found.` });
    }
    res.json({ success: true, data: updated });
  } catch (err) {
    next(err);
  }
};

export const getDailyStatistics = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const days = parseInt(req.query.days) || 30;
    const stats = await mouseService.getDailyStats(mouseId, days);
    res.json({ success: true, mouseId, days, data: stats });
  } catch (err) {
    next(err);
  }
};

export const getWeeklyStatistics = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const stats = await mouseService.getWeeklyStats(mouseId);
    res.json({ success: true, mouseId, data: stats });
  } catch (err) {
    next(err);
  }
};

export const getMonthlyStatistics = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const stats = await mouseService.getMonthlyStats(mouseId);
    res.json({ success: true, mouseId, data: stats });
  } catch (err) {
    next(err);
  }
};

export const getSessions = async (req, res, next) => {
  try {
    const mouseId = req.params.id;
    const limit = parseInt(req.query.limit) || 20;
    const sessions = await mouseService.getSessions(mouseId, limit);
    res.json({ success: true, mouseId, data: sessions });
  } catch (err) {
    next(err);
  }
};
