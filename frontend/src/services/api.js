const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:5000").replace(/\/$/, "");

async function handleResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    let message = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.message) message = parsed.message;
    } catch {
      if (errorText) message = errorText;
    }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    return handleResponse(res);
  },

  async getMouse(mouseId = "portronics-default-01") {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}`);
    return handleResponse(res);
  },

  async updateMouse(mouseId, updateData) {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updateData),
    });
    return handleResponse(res);
  },

  async getDailyStats(mouseId = "portronics-default-01", days = 14) {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}/statistics/daily?days=${days}`);
    return handleResponse(res);
  },

  async getWeeklyStats(mouseId = "portronics-default-01") {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}/statistics/weekly`);
    return handleResponse(res);
  },

  async getMonthlyStats(mouseId = "portronics-default-01") {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}/statistics/monthly`);
    return handleResponse(res);
  },

  async getSessions(mouseId = "portronics-default-01", limit = 10) {
    const res = await fetch(`${API_BASE}/api/mice/${mouseId}/sessions?limit=${limit}`);
    return handleResponse(res);
  },
};
