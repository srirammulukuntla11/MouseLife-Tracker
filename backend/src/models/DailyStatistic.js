import mongoose from "mongoose";

const dailyStatisticSchema = new mongoose.Schema(
  {
    mouseId: {
      type: String,
      required: true,
      index: true,
      trim: true,
    },
    date: {
      type: String,
      required: true, // Format: YYYY-MM-DD
      trim: true,
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

// Compound unique index ensuring one record per mouse per calendar day
dailyStatisticSchema.index({ mouseId: 1, date: 1 }, { unique: true });

export const DailyStatistic = mongoose.model("DailyStatistic", dailyStatisticSchema);
