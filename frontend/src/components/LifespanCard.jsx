import React from "react";
import { Gauge, CheckCircle2, AlertTriangle } from "lucide-react";

export function LifespanCard({ mouse }) {
  const rated = mouse?.ratedClicks || 3000000;
  const total = mouse?.totalClicks || 0;
  const remaining = Math.max(rated - total, 0);
  const lifeUsed = rated > 0 ? Number(((total / rated) * 100).toFixed(2)) : 0;
  const clampedProgress = Math.min(lifeUsed, 100);

  const isWarning = lifeUsed > 75;
  const isCritical = lifeUsed > 95;

  return (
    <div className="glass-panel lifespan-panel">
      <div className="lifespan-info">
        <h3>
          <Gauge size={22} color="#06b6d4" />
          <span>Mouse Hardware Lifespan Tracker</span>
        </h3>
        <p className="lifespan-meta">
          Monitors switch wear against manufacturer ratings. Initial target mouse is a{" "}
          <strong style={{ color: "#f8fafc" }}>Portronics Optical Mouse</strong> rated for{" "}
          <strong style={{ color: "#38bdf8" }}>{Number(rated).toLocaleString()} clicks</strong>.
        </p>

        {/* Progress Bar */}
        <div>
          <div className="progress-track">
            <div
              className={`progress-fill ${isWarning ? "warning" : ""}`}
              style={{ width: `${clampedProgress}%` }}
            />
          </div>
          <div className="lifespan-numbers">
            <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
              {isCritical ? (
                <span style={{ color: "#f43f5e", display: "inline-flex", alignItems: "center", gap: 3 }}>
                  <AlertTriangle size={14} /> High switch wear
                </span>
              ) : (
                <span style={{ color: "#10b981", display: "inline-flex", alignItems: "center", gap: 3 }}>
                  <CheckCircle2 size={14} /> Switch health optimal
                </span>
              )}
            </span>
            <span style={{ fontWeight: 700, color: isWarning ? "#fbbf24" : "#38bdf8" }}>
              {lifeUsed}% of Rated Life Consumed
            </span>
          </div>
        </div>
      </div>

      <div className="lifespan-stats-col">
        <div className="stat-box">
          <div className="stat-box-label">Rated Lifespan</div>
          <div className="stat-box-val">{Number(rated).toLocaleString()}</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Clicks Remaining</div>
          <div className="stat-box-val" style={{ color: "#34d399" }}>
            {Number(remaining).toLocaleString()}
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Tracked Clicks</div>
          <div className="stat-box-val" style={{ color: "#93c5fd" }}>
            {Number(total).toLocaleString()}
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Lifespan Used</div>
          <div className="stat-box-val" style={{ color: isWarning ? "#f59e0b" : "#a78bfa" }}>
            {lifeUsed}%
          </div>
        </div>
      </div>
    </div>
  );
}
