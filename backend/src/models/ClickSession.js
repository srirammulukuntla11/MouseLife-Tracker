import mongoose from "mongoose";

const clickSessionSchema = new mongoose.Schema(
  {
    sessionId: {
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
    startedAt: {
      type: Date,
      required: true,
      default: Date.now,
    },
    endedAt: {
      type: Date,
    },
    duration: {
      type: Number, // Duration in seconds
      default: 0,
    },
    leftClicks: {
      type: Number,
      default: 0,
      min: 0,
    },
    rightClicks: {
      type: Number,
      default: 0,
      min: 0,
    },
    middleClicks: {
      type: Number,
      default: 0,
      min: 0,
    },
    totalClicks: {
      type: Number,
      default: 0,
      min: 0,
    },
  },
  {
    timestamps: true,
  }
);

export const ClickSession = mongoose.model("ClickSession", clickSessionSchema);
