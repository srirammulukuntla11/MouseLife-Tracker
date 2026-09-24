import React from "react";
import { Clock, History } from "lucide-react";

export function SessionsTable({ sessions = [] }) {
  const formatDuration = (seconds) => {
    if (!seconds || seconds <= 0) return "< 1m";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins === 0) return `${secs}s`;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (isoString) => {
    if (!isoString) return "N/A";
    const d = new Date(isoString);
    return d.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="glass-panel sessions-card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <History size={20} color="#38bdf8" />
          <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>Recent Tracking Sessions</h3>
        </div>
        <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
          Showing latest {sessions.length} sessions
        </span>
      </div>

      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>Session ID</th>
              <th>Started At</th>
              <th>Duration</th>
              <th style={{ textAlign: "right" }}>Left</th>
              <th style={{ textAlign: "right" }}>Right</th>
              <th style={{ textAlign: "right" }}>Middle</th>
              <th style={{ textAlign: "right" }}>Total Clicks</th>
            </tr>
          </thead>
          <tbody>
            {sessions.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
                  No session history recorded yet. Agent tracks sessions continuously in background.
                </td>
              </tr>
            ) : (
              sessions.map((sess) => (
                <tr key={sess.sessionId}>
                  <td className="font-mono" style={{ color: "#38bdf8", fontSize: "0.8rem" }}>
                    {sess.sessionId.substring(0, 10)}...
                  </td>
                  <td>{formatDate(sess.startedAt)}</td>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "#94a3b8" }}>
                      <Clock size={13} />
                      {formatDuration(sess.duration)}
                    </span>
                  </td>
                  <td style={{ textAlign: "right", color: "#93c5fd" }} className="font-mono">
                    {sess.leftClicks?.toLocaleString() || 0}
                  </td>
                  <td style={{ textAlign: "right", color: "#d8b4fe" }} className="font-mono">
                    {sess.rightClicks?.toLocaleString() || 0}
                  </td>
                  <td style={{ textAlign: "right", color: "#6ee7b7" }} className="font-mono">
                    {sess.middleClicks?.toLocaleString() || 0}
                  </td>
                  <td style={{ textAlign: "right", color: "#ffffff", fontWeight: 700 }} className="font-mono">
                    {sess.totalClicks?.toLocaleString() || 0}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
