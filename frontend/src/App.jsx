import React, { useState, useEffect, useCallback } from "react";
import { api } from "./services/api";
import { Header } from "./components/Header";
import { TotalClicksCard } from "./components/TotalClicksCard";
import { ClickTypeCards } from "./components/ClickTypeCards";
import { LifespanCard } from "./components/LifespanCard";
import { ActivityCharts } from "./components/ActivityCharts";
import { SessionsTable } from "./components/SessionsTable";
import { EditMouseModal } from "./components/EditMouseModal";
import { AlertTriangle, HardDrive, Cpu, ShieldCheck } from "lucide-react";

export default function App() {
  const [mouse, setMouse] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [weeklyStats, setWeeklyStats] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [sessions, setSessions] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch all live dashboard data
  const loadDashboardData = useCallback(async (isSilent = false) => {
    if (!isSilent) setIsRefreshing(true);

    try {
      // 1. Fetch Mouse details
      const mouseRes = await api.getMouse("portronics-default-01");
      if (mouseRes.success) {
        setMouse(mouseRes.data);
      }

      // 2. Fetch Daily Stats
      const dailyRes = await api.getDailyStats("portronics-default-01", 14);
      if (dailyRes.success) {
        setDailyStats(dailyRes.data || []);
      }

      // 3. Fetch Weekly Stats
      const weeklyRes = await api.getWeeklyStats("portronics-default-01");
      if (weeklyRes.success) {
        setWeeklyStats(weeklyRes.data || []);
      }

      // 4. Fetch Monthly Stats
      const monthlyRes = await api.getMonthlyStats("portronics-default-01");
      if (monthlyRes.success) {
        setMonthlyStats(monthlyRes.data || []);
      }

      // 5. Fetch Sessions
      const sessRes = await api.getSessions("portronics-default-01", 10);
      if (sessRes.success) {
        setSessions(sessRes.data || []);
      }

      setIsOnline(true);
    } catch (err) {
      console.warn("Dashboard sync notice (backend offline or connecting):", err.message);
      setIsOnline(false);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Real-time polling loop (every 3 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData(true);
    }, 3000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  const handleSaveMouseSettings = async (updateData) => {
    const res = await api.updateMouse("portronics-default-01", updateData);
    if (res.success) {
      setMouse(res.data);
    }
  };

  if (isLoading && !mouse) {
    return (
      <div style={{ display: "flex", height: "100vh", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16 }}>
        <div style={{ width: 44, height: 44, border: "3px solid rgba(255,255,255,0.1)", borderTopColor: "#06b6d4", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
        <p style={{ color: "#94a3b8", fontSize: "0.95rem" }}>Connecting to MouseLife Tracker Service...</p>
        <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <Header
        mouse={mouse}
        isOnline={isOnline}
        isRefreshing={isRefreshing}
        onRefresh={() => loadDashboardData(false)}
        onOpenSettings={() => setIsModalOpen(true)}
      />

      {/* Offline Alert Banner */}
      {!isOnline && (
        <div className="alert-banner banner-warning">
          <AlertTriangle size={20} />
          <div>
            <strong>Backend API Offline:</strong> Windows Agent continues counting clicks locally in SQLite.
            All offline clicks will automatically synchronize as soon as the backend service reconnects.
          </div>
        </div>
      )}

      {/* Metric Cards Top Grid */}
      <section className="stats-grid">
        <TotalClicksCard
          totalClicks={mouse?.totalClicks || 0}
          ratedClicks={mouse?.ratedClicks || 3000000}
        />
        <ClickTypeCards
          leftClicks={mouse?.leftClicks || 0}
          rightClicks={mouse?.rightClicks || 0}
          middleClicks={mouse?.middleClicks || 0}
          totalClicks={mouse?.totalClicks || 0}
        />
      </section>

      {/* Hardware Lifespan Progress Panel */}
      <section>
        <LifespanCard mouse={mouse} />
      </section>

      {/* Activity Timeline and Button Ratio Charts */}
      <section>
        <ActivityCharts
          dailyData={dailyStats}
          weeklyData={weeklyStats}
          monthlyData={monthlyStats}
          mouse={mouse}
        />
      </section>

      {/* Recent Tracking Sessions */}
      <section>
        <SessionsTable sessions={sessions} />
      </section>

      {/* System Hardware Details Footer */}
      <footer className="glass-panel" style={{ padding: "1.25rem 1.75rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", fontSize: "0.82rem", color: "#64748b" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <HardDrive size={15} color="#06b6d4" /> Local Engine: SQLite WAL Mode
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <Cpu size={15} color="#8b5cf6" /> Sync: Batch Idempotency
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
            <ShieldCheck size={15} color="#10b981" /> Zero Privacy Intrusion
          </span>
        </div>
        <div>
          MouseLife Tracker v1.0.0 &bull; Portronics Hardware Lifespan System
        </div>
      </footer>

      {/* Settings Modal */}
      <EditMouseModal
        mouse={mouse}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveMouseSettings}
      />
    </div>
  );
}
