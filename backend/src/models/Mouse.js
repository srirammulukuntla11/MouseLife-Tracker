import mongoose from "mongoose";

const mouseSchema = new mongoose.Schema(
  {
    mouseId: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      index: true,
    },
    name: {
      type: String,
      required: true,
      default: "Portronics Wireless Mouse",
      trim: true,
    },
    manufacturer: {
      type: String,
      default: "Portronics",
      trim: true,
    },
    model: {
      type: String,
      default: "Toad 23 / Wireless Optical",
      trim: true,
    },
    ratedClicks: {
      type: Number,
      default: 3000000,
      min: 1,
    },
    totalClicks: {
      type: Number,
      default: 0,
      min: 0,
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
    trackingStartedAt: {
      type: Date,
      default: Date.now,
    },
    lastSyncedAt: {
      type: Date,
      default: Date.now,
    },
  },
  {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true },
  }
);

// Virtual calculation for remaining clicks: max(ratedClicks - totalClicks, 0)
mouseSchema.virtual("remainingClicks").get(function () {
  const rated = this.ratedClicks || 3000000;
  const total = this.totalClicks || 0;
  return Math.max(rated - total, 0);
});

// Virtual calculation for life used percentage: (totalClicks / ratedClicks) * 100
mouseSchema.virtual("lifeUsedPercentage").get(function () {
  const rated = this.ratedClicks || 3000000;
  const total = this.totalClicks || 0;
  if (rated <= 0) return 0;
  return Number(((total / rated) * 100).toFixed(2));
});

export const Mouse = mongoose.model("Mouse", mouseSchema);
