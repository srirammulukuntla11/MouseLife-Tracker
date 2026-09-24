import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { BarChart3, PieChart as PieIcon, Calendar } from "lucide-react";

export function ActivityCharts({ dailyData = [], weeklyData = [], monthlyData = [], mouse }) {
  const [activeTab, setActiveTab] = useState("daily"); // 'daily' | 'weekly' | 'monthly'

  // Prepare chart data based on active tab
  const getActiveChartData = () => {
    if (activeTab === "weekly") {
      return weeklyData.length > 0 ? weeklyData : [{ week: "No Data", totalClicks: 0 }];
    }
    if (activeTab === "monthly") {
      return monthlyData.length > 0 ? monthlyData : [{ month: "No Data", totalClicks: 0 }];
    }
    return dailyData.length > 0 ? dailyData : [{ date: "Today", totalClicks: 0 }];
  };

  const currentChartData = getActiveChartData();
  const xKey = activeTab === "weekly" ? "week" : activeTab === "monthly" ? "month" : "date";

  // Pie chart data for button distribution
  const pieData = [
    { name: "Left Click", value: mouse?.leftClicks || 0, color: "#3b82f6" },
    { name: "Right Click", value: mouse?.rightClicks || 0, color: "#a855f7" },
    { name: "Middle Click", value: mouse?.middleClicks || 0, color: "#10b981" },
  ];
  const hasPieData = pieData.some((p) => p.value > 0);

  // Custom Dark Tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div
          style={{
            background: "#1e293b",
            border: "1px solid rgba(255,255,255,0.1)",
            padding: "8px 12px",
            borderRadius: "8px",
            boxShadow: "0 8px 16px rgba(0,0,0,0.5)",
          }}
        >
          <div style={{ color: "#94a3b8", fontSize: "0.75rem", marginBottom: 4 }}>{label}</div>
          <div style={{ color: "#38bdf8", fontWeight: 700, fontSize: "0.95rem" }}>
            {payload[0].value.toLocaleString()} Clicks
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="analytics-grid">
      {/* Activity Timeline Bar Chart */}
      <div className="glass-panel chart-card">
        <div className="chart-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <BarChart3 size={20} color="#6366f1" />
            <span className="chart-title">Click Volume Analytics</span>
          </div>

          <div className="chart-tabs">
            <button
              className={`chart-tab-btn ${activeTab === "daily" ? "active" : ""}`}
              onClick={() => setActiveTab("daily")}
            >
              Daily
            </button>
            <button
              className={`chart-tab-btn ${activeTab === "weekly" ? "active" : ""}`}
              onClick={() => setActiveTab("weekly")}
            >
              Weekly
            </button>
            <button
              className={`chart-tab-btn ${activeTab === "monthly" ? "active" : ""}`}
              onClick={() => setActiveTab("monthly")}
            >
              Monthly
            </button>
          </div>
        </div>

        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={currentChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0.6} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="totalClicks" fill="url(#barGradient)" radius={[4, 4, 0, 0]} maxBarSize={45} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Button Ratio Donut Chart */}
      <div className="glass-panel chart-card">
        <div className="chart-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <PieIcon size={20} color="#a855f7" />
            <span className="chart-title">Button Ratio</span>
          </div>
        </div>

        <div style={{ width: "100%", height: 260, display: "flex", alignItems: "center", justifyContent: "center" }}>
          {!hasPieData ? (
            <div style={{ textAlign: "center", color: "#64748b", fontSize: "0.85rem" }}>
              No click data yet.<br />Use mouse to populate ratio.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: "0.8rem", color: "#94a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
