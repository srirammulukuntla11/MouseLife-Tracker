import React from "react";
import { ArrowLeft, ArrowRight, Disc3 } from "lucide-react";

export function ClickTypeCards({ leftClicks = 0, rightClicks = 0, middleClicks = 0, totalClicks = 0 }) {
  const calcPercent = (count) => {
    if (!totalClicks || totalClicks <= 0) return "0.0%";
    return `${((count / totalClicks) * 100).toFixed(1)}%`;
  };

  return (
    <>
      {/* Left Click Card */}
      <div className="glass-panel metric-card card-left">
        <div>
          <div className="metric-header">
            <span>Left Clicks</span>
            <div className="metric-icon-box" style={{ background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa" }}>
              <ArrowLeft size={18} />
            </div>
          </div>
          <div className="metric-value font-mono" style={{ color: "#93c5fd" }}>
            {Number(leftClicks).toLocaleString()}
          </div>
        </div>
        <div className="metric-footer">
          <span>Primary Action</span>
          <span className="badge-percent" style={{ background: "rgba(59, 130, 246, 0.2)", color: "#bfdbfe" }}>
            {calcPercent(leftClicks)}
          </span>
        </div>
      </div>

      {/* Right Click Card */}
      <div className="glass-panel metric-card card-right">
        <div>
          <div className="metric-header">
            <span>Right Clicks</span>
            <div className="metric-icon-box" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc" }}>
              <ArrowRight size={18} />
            </div>
          </div>
          <div className="metric-value font-mono" style={{ color: "#d8b4fe" }}>
            {Number(rightClicks).toLocaleString()}
          </div>
        </div>
        <div className="metric-footer">
          <span>Context Menu</span>
          <span className="badge-percent" style={{ background: "rgba(168, 85, 247, 0.2)", color: "#e9d5ff" }}>
            {calcPercent(rightClicks)}
          </span>
        </div>
      </div>

      {/* Middle Click Card */}
      <div className="glass-panel metric-card card-middle">
        <div>
          <div className="metric-header">
            <span>Middle Clicks</span>
            <div className="metric-icon-box" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#34d399" }}>
              <Disc3 size={18} />
            </div>
          </div>
          <div className="metric-value font-mono" style={{ color: "#6ee7b7" }}>
            {Number(middleClicks).toLocaleString()}
          </div>
        </div>
        <div className="metric-footer">
          <span>Scroll Wheel Press</span>
          <span className="badge-percent" style={{ background: "rgba(16, 185, 129, 0.2)", color: "#a7f3d0" }}>
            {calcPercent(middleClicks)}
          </span>
        </div>
      </div>
    </>
  );
}
