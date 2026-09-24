import React from "react";
import { MousePointer, RefreshCw, Settings, ShieldCheck, WifiOff } from "lucide-react";

export function Header({ mouse, isOnline, isRefreshing, onRefresh, onOpenSettings }) {
  // Status check: Is the backend online? Did we sync recently?
  const hasSyncedRecently = () => {
    if (!mouse?.lastSyncedAt) return false;
    const diffSeconds = (new Date().getTime() - new Date(mouse.lastSyncedAt).getTime()) / 1000;
    return diffSeconds < 60; // Synced within the last minute
  };

  return (
    <header className="glass-panel header-wrapper">
      <div className="brand-section">
        <div className="brand-icon-box">
          <MousePointer size={28} color="#ffffff" />
        </div>
        <div className="brand-text">
          <h1>MouseLife Tracker</h1>
          <div className="brand-subtitle">
            <span>{mouse?.name || "Portronics Wireless Mouse"}</span>
            <span className="mouse-badge">{mouse?.model || "Toad 23"}</span>
            <span title="Privacy Protected: No coordinates, keystrokes, or screen data" style={{ display: "inline-flex", alignItems: "center", gap: 3, fontSize: "0.75rem", color: "#10b981", marginLeft: 8 }}>
              <ShieldCheck size={14} /> Global Hook Active
            </span>
          </div>
        </div>
      </div>

      <div className="header-controls">
        {/* Real-time Tracking Status Badge */}
        {!isOnline ? (
          <div className="status-pill status-offline">
            <WifiOff size={14} />
            <span>Backend Offline</span>
          </div>
        ) : hasSyncedRecently() ? (
          <div className="status-pill status-active">
            <span className="pulse-dot" />
            <span>Tracking Active</span>
          </div>
        ) : (
          <div className="status-pill status-paused">
            <span className="pulse-dot" style={{ backgroundColor: "#fbbf24" }} />
            <span>Agent Connected</span>
          </div>
        )}

        {/* Manual Refresh Button */}
        <button
          className="btn-action"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Data"
        >
          <RefreshCw size={15} className={isRefreshing ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>

        {/* Settings Button */}
        <button
          className="btn-action"
          onClick={onOpenSettings}
          title="Configure Mouse Profile"
        >
          <Settings size={15} />
          <span>Settings</span>
        </button>
      </div>
    </header>
  );
}
