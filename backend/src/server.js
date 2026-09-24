import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import dotenv from "dotenv";
import { connectDB } from "./config/db.js";
import apiRouter from "./routes/api.js";
import { errorHandler, notFoundHandler } from "./middleware/errorHandler.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const CORS_ORIGIN = process.env.CORS_ORIGIN || "*";

// Security and utility middleware
app.use(helmet());
app.use(
  cors({
    origin: CORS_ORIGIN,
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);
app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API routes
app.use("/api", apiRouter);

// Fallback handlers
app.use(notFoundHandler);
app.use(errorHandler);

// Start server after connecting to database
const startServer = async (customPort) => {
  try {
    await connectDB();
    const listenPort = customPort || process.env.PORT || 5000;
    const server = app.listen(listenPort, () => {
      console.log(`[MouseLife Backend] Server listening on http://127.0.0.1:${listenPort}`);
    });
    return server;
  } catch (error) {
    console.error("[MouseLife Backend] Failed to start server:", error);
    process.exit(1);
  }
};

// Check if run directly
if (process.argv[1] && process.argv[1].endsWith("server.js")) {
  startServer();
}

export { app, startServer };
