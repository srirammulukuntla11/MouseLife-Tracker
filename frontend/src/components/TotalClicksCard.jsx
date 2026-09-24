import React from "react";
import { Activity, Zap } from "lucide-react";

export function TotalClicksCard({ totalClicks = 0, ratedClicks = 3000000 }) {
  const formattedTotal = Number(totalClicks).toLocaleString();

  return (
    <div className="glass-panel metric-card card-total">
      <div>
        <div className="metric-header">
          <span>Total Clicks Tracked</span>
          <div className="metric-icon-box" style={{ background: "rgba(99, 102, 241, 0.15)", color: "#818cf8" }}>
            <Activity size={18} />
          </div>
        </div>
        <div className="metric-value font-mono" style={{ color: "#ffffff" }}>
          {formattedTotal}
        </div>
      </div>
      <div className="metric-footer">
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <Zap size={14} color="#06b6d4" />
          <span>Real-time Hardware Global Clicks</span>
        </span>
        <span className="badge-percent" style={{ background: "rgba(99, 102, 241, 0.2)", color: "#c7d2fe" }}>
          Active
        </span>
      </div>
    </div>
  );
}
