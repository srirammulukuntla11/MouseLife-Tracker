import mongoose from "mongoose";

const syncBatchSchema = new mongoose.Schema(
  {
    batchId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    mouseId: {
      type: String,
      required: true,
      index: true,
      trim: true,
    },
    clientSessionId: {
      type: String,
      trim: true,
    },
    leftClicks: {
      type: Number,
      required: true,
      default: 0,
    },
    rightClicks: {
      type: Number,
      required: true,
      default: 0,
    },
    middleClicks: {
      type: Number,
      required: true,
      default: 0,
    },
    totalClicks: {
      type: Number,
      required: true,
      default: 0,
    },
    clientTimestamp: {
      type: String,
    },
    syncedAt: {
      type: Date,
      default: Date.now,
    },
  },
  {
    timestamps: true,
  }
);

export const SyncBatch = mongoose.model("SyncBatch", syncBatchSchema);
