import React, { useState } from "react";
import { X, Save, Sliders } from "lucide-react";

export function EditMouseModal({ mouse, isOpen, onClose, onSave }) {
  if (!isOpen) return null;

  const [name, setName] = useState(mouse?.name || "Portronics Wireless Mouse");
  const [model, setModel] = useState(mouse?.model || "Toad 23 / Wireless Optical");
  const [ratedClicks, setRatedClicks] = useState(mouse?.ratedClicks || 3000000);
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await onSave({
        name,
        model,
        ratedClicks: Number(ratedClicks),
      });
      onClose();
    } catch (err) {
      alert(`Failed to update profile: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Sliders size={20} color="#06b6d4" />
            <h3>Configure Hardware Profile</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Mouse Device Name</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Model Description</label>
            <input
              type="text"
              className="form-input"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Manufacturer Rated Clicks</label>
            <input
              type="number"
              className="form-input font-mono"
              value={ratedClicks}
              min={1000}
              step={100000}
              onChange={(e) => setRatedClicks(e.target.value)}
              required
            />
            <span style={{ fontSize: "0.75rem", color: "#64748b", marginTop: 4, display: "block" }}>
              Standard Portronics rated click lifespan is 3,000,000 clicks.
            </span>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-action" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-action btn-primary" disabled={isSaving}>
              <Save size={16} />
              <span>{isSaving ? "Saving..." : "Save Settings"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
